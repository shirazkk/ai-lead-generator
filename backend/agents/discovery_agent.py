import asyncio
import logging
from typing import List, Optional
from models import RawBusiness
from services.places_service import search_places

logger = logging.getLogger(__name__)

NEIGHBOURHOODS = {
    "karachi": ["Defence", "Gulshan", "Clifton", "North Nazimabad", "Saddar", "Korangi", "Gulberg", "Malir"],
    "lahore": ["DHA", "Gulberg", "Model Town", "Johar Town", "Bahria Town", "Iqbal Town", "Garden Town", "Cantt"],
    "islamabad": ["F-7", "F-10", "G-11", "Blue Area", "DHA", "Bahria Town", "E-11", "F-6"],
    "dubai": ["Deira", "Bur Dubai", "Jumeirah", "Al Barsha", "Downtown", "Mirdif", "Karama", "Silicon Oasis"],
    "london": ["Shoreditch", "Brixton", "Hackney", "Peckham", "Croydon", "Ealing", "Islington", "Lewisham"],
    "new york": ["Brooklyn", "Queens", "Bronx", "Harlem", "Astoria", "Flushing", "Bushwick", "Williamsburg"],
    "los angeles": ["Downtown", "Compton", "East LA", "Van Nuys", "Inglewood", "Watts", "Boyle Heights", "Koreatown"],
    "chicago": ["Pilsen", "Hyde Park", "Rogers Park", "Wicker Park", "Logan Square", "Bronzeville", "Avondale", "Englewood"],
    "toronto": ["Scarborough", "North York", "Etobicoke", "Mississauga", "Brampton", "Vaughan", "Markham", "Ajax"],
    "sydney": ["Parramatta", "Bankstown", "Blacktown", "Liverpool", "Penrith", "Campbelltown", "Auburn", "Fairfield"],
}

def extract_business(place: dict, city: str, business_type: str) -> Optional[RawBusiness]:
    # Only keep businesses with no website
    if place.get("websiteUri"):
        return None
    
    # Skip permanently closed businesses
    if place.get("businessStatus") == "CLOSED_PERMANENTLY":
        return None

    name = place.get("displayName", {}).get("text", "")
    address = place.get("formattedAddress", "")
    phone = place.get("nationalPhoneNumber") or place.get("internationalPhoneNumber")
    rating = place.get("rating")
    maps_url = place.get("googleMapsUri", "")
    place_id = place.get("id", "")
    description = place.get("editorialSummary", {}).get("text", "")

    if not name or not address:
        return None

    return RawBusiness(
        business_name=name,
        business_type=business_type,
        address=address,
        city=city,
        country=city.capitalize(), # Simplified inference, could be improved based on locale
        phone=phone,
        google_maps_url=maps_url,
        place_id=place_id,
        rating=rating,
        business_description=description,
        website_status="none",
    )

async def discover_businesses(city: str, business_type: str, count: int) -> List[RawBusiness]:
    all_businesses = []
    seen_place_ids = set()
    
    city_lower = city.lower()
    neighbourhoods = NEIGHBOURHOODS.get(city_lower, [""])
    
    for neighbourhood in neighbourhoods:
        if len(all_businesses) >= count:
            break
        
        query = f"{business_type} in {neighbourhood} {city}".strip() if neighbourhood else f"{business_type} in {city}"
        logger.info(f"Searching Places API: {query}")
        
        page_token = None
        pages_fetched = 0
        max_pages = 3  # max 3 pages per neighbourhood = 60 results
        
        while len(all_businesses) < count and pages_fetched < max_pages:
            try:
                response = await search_places(query, max_results=20, page_token=page_token)
                places = response.get("places", [])
                
                if not places:
                    break
                
                for place in places:
                    place_id = place.get("id")
                    if place_id in seen_place_ids:
                        continue
                    seen_place_ids.add(place_id)
                    
                    business = extract_business(place, city, business_type)
                    if business:
                        all_businesses.append(business)
                        logger.info(f"Found lead: {business.business_name} — no website")
                
                page_token = response.get("nextPageToken")
                if not page_token:
                    break
                
                pages_fetched += 1
                await asyncio.sleep(1)  # required between paginated requests
                
            except Exception as e:
                logger.error(f"Places API error for query '{query}': {e}")
                break
        
        await asyncio.sleep(0.5)  # small delay between neighbourhood queries
    
    logger.info(f"Discovery complete: {len(all_businesses)} leads found")
    return all_businesses[:count]
