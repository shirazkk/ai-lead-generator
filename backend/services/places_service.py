import httpx
import logging
from typing import Optional
from config import settings

logger = logging.getLogger(__name__)

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
