import logging
from typing import Optional, List
from services.firecrawl_service import scrape_url
from models import RawBusiness, EnrichedBusiness

logger = logging.getLogger(__name__)

async def enrich_business(raw_business: RawBusiness) -> EnrichedBusiness:
    logger.info(f"Scraper Agent: Enriching '{raw_business.business_name}' via Firecrawl")

    # 1. Prepare prompts
    maps_prompt = "Extract the business hours and the owner name if mentioned."
    yelp_prompt = "Extract the business description, top 3 customer reviews, and the business rating."
    social_prompt = "Extract the owner name, contact email address, and the about/bio section."

    # 2. Find Yelp and social profiles if not present
    yelp_url = raw_business.yelp_url
    social_urls = raw_business.social_urls or []

    if not yelp_url or not social_urls:
        from services.firecrawl_service import search_business_urls
        found_urls = await search_business_urls(raw_business.business_name, raw_business.city or "")
        if not yelp_url and found_urls.get("yelp_url"):
            yelp_url = found_urls["yelp_url"]
        if not social_urls and found_urls.get("social_urls"):
            social_urls = found_urls["social_urls"]

    # 3. Scrape from sources
    maps_data = {}
    if raw_business.google_maps_url:
        maps_data = await scrape_url(raw_business.google_maps_url, maps_prompt)
        
    yelp_data = {}
    if yelp_url:
        yelp_data = await scrape_url(yelp_url, yelp_prompt)
        
    social_data_list = []
    for s_url in social_urls:
        social_data = await scrape_url(s_url, social_prompt)
        if social_data:
            social_data_list.append(social_data)


    # Extracting fields with robust lookups
    # Firecrawl returns camelCase (e.g., ownerName), mapping to snake_case
    owner = maps_data.get('ownerName') or next((s.get('ownerName') for s in social_data_list if s.get('ownerName')), None)
    email = next((s.get('email') for s in social_data_list if s.get('email')), None)
    description = yelp_data.get('description') or maps_data.get('editorialSummary') or maps_data.get('description')

    return EnrichedBusiness(
        id=raw_business.id,
        business_name=raw_business.business_name,
        business_type=raw_business.business_type,
        address=raw_business.address,
        phone=raw_business.phone,
        website=raw_business.website,
        rating=raw_business.rating or yelp_data.get('rating', 0.0),
        google_maps_url=raw_business.google_maps_url,
        website_status=raw_business.website_status,
        city=raw_business.city,
        country=raw_business.country,
        owner_name=owner,
        email=email,
        social_profiles=social_urls,
        business_description=description,
        reviews=yelp_data.get('reviews', [])
    )

