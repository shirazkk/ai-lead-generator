import httpx
import logging
import json
import asyncio
from typing import Optional, List
from config import settings

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------ #
# In-memory cache — avoids hitting free API limits on repeated searches
# ------------------------------------------------------------------ #
NEIGHBOURHOODS_CACHE: dict = {}

PLACES_API_KEY = settings.google_places_api_key
PLACES_BASE_URL = "https://places.googleapis.com/v1/places:searchText"
PLACE_DETAILS_URL = "https://places.googleapis.com/v1/places/{place_id}"

FIELD_MASK = ",".join([
    "places.id",
    "places.displayName",
    "places.formattedAddress",
    "places.nationalPhoneNumber",
    "places.internationalPhoneNumber",
    "places.websiteUri",
    "places.rating",
    "places.googleMapsUri",
    "places.businessStatus",
    "places.types",
    "places.regularOpeningHours",
    "places.editorialSummary",
])


# ================================================================== #
# Google Places API                                                   #
# ================================================================== #

async def search_places(
    query: str,
    max_results: int = 20,
    page_token: Optional[str] = None,
) -> dict:
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": PLACES_API_KEY,
        "X-Goog-FieldMask": FIELD_MASK,
    }
    body = {
        "textQuery": query,
        "maxResultCount": min(max_results, 20),
        "languageCode": "en",
    }
    if page_token:
        body["pageToken"] = page_token

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(PLACES_BASE_URL, json=body, headers=headers)
        response.raise_for_status()
        return response.json()


async def get_place_details(place_id: str) -> dict:
    headers = {
        "X-Goog-Api-Key": PLACES_API_KEY,
        "X-Goog-FieldMask": (
            "id,displayName,formattedAddress,nationalPhoneNumber,"
            "websiteUri,rating,googleMapsUri,editorialSummary"
        ),
    }
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(
            PLACE_DETAILS_URL.format(place_id=place_id),
            headers=headers,
        )
        response.raise_for_status()
        return response.json()


# ================================================================== #
# Neighbourhood discovery — fallback chain                           #
# ================================================================== #

async def fetch_neighbourhoods(city: str) -> List[str]:
    """
    Fetch neighbourhood/district names for any city in the world.

    Uses a 4-strategy fallback chain so it works regardless of how well
    the city is mapped in OpenStreetMap:

      1. Overpass API  — best for well-mapped Western/South-Asian cities
      2. Nominatim API — broader city matching, different OSM endpoint
      3. Gemini AI     — covers any city in the world from training data
      4. Empty list    — caller falls back to single city-wide search

    Results are cached in memory so repeated searches don't hit the APIs.
    """
    city_lower = city.lower().strip()

    if city_lower in NEIGHBOURHOODS_CACHE:
        logger.info(f"[neighbourhoods] Returning cached result for: {city}")
        return NEIGHBOURHOODS_CACHE[city_lower]

    # Strategy 1 — Overpass
    logger.info(f"[neighbourhoods] Strategy 1: Overpass API for '{city}'")
    result = await _fetch_overpass(city)
    if result:
        logger.info(f"[neighbourhoods] Overpass succeeded: {len(result)} neighbourhoods")
        NEIGHBOURHOODS_CACHE[city_lower] = result
        return result

    # Strategy 2 — Nominatim
    logger.info(f"[neighbourhoods] Strategy 2: Nominatim API for '{city}'")
    result = await _fetch_nominatim(city)
    if result:
        logger.info(f"[neighbourhoods] Nominatim succeeded: {len(result)} neighbourhoods")
        NEIGHBOURHOODS_CACHE[city_lower] = result
        return result

    # Strategy 3 — Gemini
    logger.info(f"[neighbourhoods] Strategy 3: Gemini AI for '{city}'")
    result = await _fetch_gemini(city)
    if result:
        logger.info(f"[neighbourhoods] Gemini succeeded: {len(result)} neighbourhoods")
        NEIGHBOURHOODS_CACHE[city_lower] = result
        return result

    # Strategy 4 — give up, let caller do city-wide search
    logger.warning(
        f"[neighbourhoods] All strategies failed for '{city}'. "
        f"Caller will fall back to city-wide search."
    )
    NEIGHBOURHOODS_CACHE[city_lower] = []
    return []


# ================================================================== #
# Strategy 1 — Overpass                                              #
# ================================================================== #

async def _fetch_overpass(city: str) -> List[str]:
    """
    Query OpenStreetMap Overpass API for neighbourhood nodes/ways.

    Covers: suburb, neighbourhood, quarter, city_district, borough.
    Uses case-insensitive city name match and admin_level 4-8.
    Prefers English names (name:en) over local script names.
    """
    try:
        # FIX: removed quotes around i flag for case-insensitive matching
        query = f"""[out:json][timeout:25];
area["name"~"^{city}$",i]["admin_level"~"^(4|5|6|7|8)$"]->.a;
(
  node(area.a)["place"~"^(suburb|neighbourhood|quarter|city_district|borough)$"];
  way(area.a)["place"~"^(suburb|neighbourhood|quarter|city_district|borough)$"];
);
out tags;"""

        headers = {
            "User-Agent": "AILeadGen/1.0 (Contact: shirazkk8@gmail.com)",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        # Simple retry mechanism
        for i in range(3):
            try:
                async with httpx.AsyncClient(timeout=45) as client:
                    response = await client.post(
                        "https://overpass-api.de/api/interpreter",
                        data={"data": query},
                        headers=headers,
                    )
                    # 429 Too Many Requests, 503 Service Unavailable, 504 Gateway Timeout
                    if response.status_code in [429, 503, 504]:
                        await asyncio.sleep(2 ** i)
                        continue
                    
                    response.raise_for_status()
                    data = response.json()
                    return _extract_names(data.get("elements", []))
            except httpx.HTTPError as e:
                if i == 2: raise e
                await asyncio.sleep(2 ** i)
        return []

    except Exception as e:
        logger.warning(f"[overpass] Failed for '{city}': {e}")
        return []


# ================================================================== #
# Strategy 2 — Nominatim                                             #
# ================================================================== #

async def _fetch_nominatim(city: str) -> List[str]:
    """
    Query Nominatim (OSM geocoder) to find the city boundary, then
    query Overpass using the resolved OSM relation ID.

    This is more reliable than the direct Overpass area lookup because
    Nominatim handles city name variations and aliases better.
    """
    try:
        headers = {
            "User-Agent": "AILeadGen/1.0 (Contact: shirazkk8@gmail.com)",
            "Accept-Language": "en",
        }

        # Step 1: resolve city → OSM relation ID
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(
                "https://nominatim.openstreetmap.org/search",
                params={
                    "q": city,
                    "format": "json",
                    "limit": 5,
                    "featuretype": "city",
                    "addressdetails": 1,
                },
                headers=headers,
            )
            response.raise_for_status()
            results = response.json()

        # Pick the first result that is a city/town/administrative area
        osm_id = None
        for r in results:
            if r.get("osm_type") == "relation" and r.get("class") in ("place", "boundary"):
                osm_id = r.get("osm_id")
                break

        if not osm_id:
            logger.warning(f"[nominatim] No relation found for '{city}'")
            return []

        # FIX: calculate area_id in Python first
        area_id = 3600000000 + int(osm_id)

        # Step 2: use the area ID to query Overpass for sub-areas
        query = f"""[out:json][timeout:25];
area({area_id})->.city;
(
  node(area.city)["place"~"^(suburb|neighbourhood|quarter|city_district|borough)$"];
  way(area.city)["place"~"^(suburb|neighbourhood|quarter|city_district|borough)$"];
);
out tags;"""

        overpass_headers = {
            "User-Agent": "AILeadGen/1.0 (Contact: shirazkk8@gmail.com)",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        # Simple retry mechanism
        for i in range(3):
            try:
                async with httpx.AsyncClient(timeout=45) as client:
                    response = await client.post(
                        "https://overpass-api.de/api/interpreter",
                        data={"data": query},
                        headers=overpass_headers,
                    )
                    # 429 Too Many Requests, 503 Service Unavailable, 504 Gateway Timeout
                    if response.status_code in [429, 503, 504]:
                        await asyncio.sleep(2 ** i)
                        continue
                    
                    response.raise_for_status()
                    data = response.json()
                    return _extract_names(data.get("elements", []))
            except httpx.HTTPError as e:
                if i == 2: raise e
                await asyncio.sleep(2 ** i)
        return []

    except Exception as e:
        logger.warning(f"[nominatim] Failed for '{city}': {e}")
        return []


# ================================================================== #
# Strategy 3 — Gemini AI                                             #
# ================================================================== #

async def _fetch_gemini(city: str) -> List[str]:
    """
    Ask OpenRouter to list well-known neighbourhoods for the city.

    Uses OpenRouter instead of Gemini to avoid competing with the
    lead analysis quota. Falls back gracefully on any error.
    """
    try:
        prompt = f"""You are a geographic data extraction tool.
Return ONLY a raw JSON array of 12 strings, where each string is a well-known neighbourhood or district in {city}.
Do not include any conversational filler, explanations, markdown, or code fences.
Output only the JSON array: ["Neighbourhood 1", "Neighbourhood 2", ...]"""

        headers = {
            "Authorization": f"Bearer {settings.openrouter_api_key}",
            "Content-Type": "application/json",
        }

        body = {
            "model": f"{settings.openrouter_model}",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 300,
            "temperature": 0.3,
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                json=body,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()

        text = data["choices"][0]["message"]["content"].strip()

        # Strip markdown fences if model adds them
        text = text.replace("```json", "").replace("```", "").strip()
        
        # Try to find JSON if not clean
        try:
            start = text.find('[')
            end = text.rfind(']') + 1
            if start != -1 and end != -1:
                text = text[start:end]
            neighbourhoods = json.loads(text)
        except json.JSONDecodeError:
            logger.error(f"[openrouter-neighbourhoods] Could not parse JSON for '{city}'. Raw text: {text}")
            return []

        if not isinstance(neighbourhoods, list):
            raise ValueError("OpenRouter did not return a list")

        # Clean and deduplicate
        result = []
        seen = set()
        for n in neighbourhoods:
            if isinstance(n, str) and n.strip():
                clean = n.strip()
                if clean.lower() not in seen:
                    seen.add(clean.lower())
                    result.append(clean)

        return result[:15]

    except Exception as e:
        logger.warning(f"[openrouter-neighbourhoods] Failed for '{city}': {e}")
        return []

# ================================================================== #
# Shared helper                                                       #
# ================================================================== #

def _extract_names(elements: list) -> List[str]:
    """
    Extract English neighbourhood names from Overpass API elements.

    Prefers name:en over local-script name to ensure the names work
    correctly in downstream Google Places API queries.
    """
    seen: set = set()
    names: List[str] = []

    for elem in elements:
        tags = elem.get("tags", {})
        # Prefer English name, fall back to default name
        name = tags.get("name:en") or tags.get("name")
        if name and isinstance(name, str):
            clean = name.strip()
            if clean.lower() not in seen:
                seen.add(clean.lower())
                names.append(clean)

    return names[:15]