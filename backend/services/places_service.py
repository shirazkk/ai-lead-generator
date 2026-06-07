import httpx
import logging
from typing import Optional, List
from config import settings

logger = logging.getLogger(__name__)

# In-memory cache for fetched city neighborhoods to avoid hitting free API limits
NEIGHBOURHOODS_CACHE = {}

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

async def search_places(query: str, max_results: int = 20, page_token: Optional[str] = None) -> dict:
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": PLACES_API_KEY,
        "X-Goog-FieldMask": FIELD_MASK,
    }
    body = {
        "textQuery": query,
        "maxResultCount": min(max_results, 20),  # API max is 20 per page
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
        "X-Goog-FieldMask": "id,displayName,formattedAddress,nationalPhoneNumber,websiteUri,rating,googleMapsUri,editorialSummary",
    }
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(
            PLACE_DETAILS_URL.format(place_id=place_id),
            headers=headers
        )
        response.raise_for_status()
        return response.json()

async def fetch_neighbourhoods(city: str) -> List[str]:
    """
    Fetch the list of neighborhood/suburb names in a city using OpenStreetMap Overpass API.
    Uses in-memory caching to avoid repeated lookups.
    Returns up to 15 neighborhoods to keep Google Places API usage reasonable.
    """
    city_lower = city.lower().strip()
    if city_lower in NEIGHBOURHOODS_CACHE:
        logger.info(f"Returning cached neighborhoods for city: {city}")
        return NEIGHBOURHOODS_CACHE[city_lower]

    logger.info(f"Fetching neighborhoods dynamically from Overpass API for city: {city}")
    neighbourhoods = []
    try:
        url = "https://overpass-api.de/api/interpreter"
        # Query for suburbs, neighbourhoods, and quarters inside the city boundary
        query = f"""[out:json][timeout:15];
area["name"="{city}"]->.a;
(
  node(area.a)["place"="suburb"];
  node(area.a)["place"="neighbourhood"];
  node(area.a)["place"="quarter"];
  way(area.a)["place"="suburb"];
  way(area.a)["place"="neighbourhood"];
  way(area.a)["place"="quarter"];
);
out tags;"""

        headers = {
            "User-Agent": "AI-Lead-Generator/1.0 (shirazkk8@gmail.com)",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(url, data={"data": query}, headers=headers)
            response.raise_for_status()
            data = response.json()

        elements = data.get("elements", [])
        for elem in elements:
            tags = elem.get("tags", {})
            name = tags.get("name")
            if name and name not in neighbourhoods:
                neighbourhoods.append(name)

        # Cap at 15 neighborhoods to keep Google Places API usage reasonable
        neighbourhoods = neighbourhoods[:15]

        logger.info(f"Overpass resolved {len(neighbourhoods)} neighborhoods for {city}: {neighbourhoods}")
        NEIGHBOURHOODS_CACHE[city_lower] = neighbourhoods
        return neighbourhoods
    except Exception as e:
        logger.error(f"Failed to fetch neighborhoods from Overpass for city '{city}': {e}")
        return []

