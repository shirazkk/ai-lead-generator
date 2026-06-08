import asyncio
import logging
from firecrawl import FirecrawlApp
from config import settings

logger = logging.getLogger(__name__)

# Initialize FirecrawlApp
app = FirecrawlApp(api_key=settings.firecrawl_api_key)

async def scrape_url(url: str, prompt: str) -> dict:
    """
    Scrapes a URL using Firecrawl and extracts data based on the provided prompt.
    Returns an empty dict on failure (including credit exhaustion).
    """
    # Filter unsupported social media domains
    social_domains = ["instagram.com", "facebook.com", "linkedin.com", "twitter.com", "tiktok.com"]
    if any(domain in url for domain in social_domains):
        logger.info(f"Skipping unsupported social URL (plan limitation): {url}")
        return {}

    try:
        logger.info(f"Firecrawl scraping {url} with prompt: {prompt}")
        schema = {
            "type": "object",
            "properties": {
                "ownerName": {"type": "string", "description": "The name of the business owner if mentioned"},
                "email": {"type": "string", "description": "The contact email address of the business"},
                "description": {"type": "string", "description": "The description of the business, services, or about info"},
                "reviews": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Top customer reviews or comments"
                },
                "rating": {"type": "number", "description": "The business rating (on 0-5 scale)"},
                "businessHours": {"type": "string", "description": "The business opening and closing hours"}
            }
        }

        # Run synchronous Firecrawl scrape in a thread pool to avoid blocking the event loop
        result = await asyncio.to_thread(
            lambda: app.scrape(
                url=url,
                formats=[{
                    "type": "json",
                    "schema": schema,
                    "prompt": prompt
                }]
            )
        )
        
        # Detailed logging of the raw result for debugging
        logger.info(f"Firecrawl raw result for {url}: {result}")
        
        # Check for success/data
        if not result:
            logger.warning(f"Firecrawl returned no response for {url}")
            return {}

        # Handle older SDK or dictionary fallback
        if isinstance(result, dict):
            # Extract 'json' nested inside 'data' or return the raw dict
            data_dict = result.get('data', {})
            if isinstance(data_dict, dict):
                return data_dict.get('json', data_dict)
            return result

        # Handle newer SDK (Pydantic Document object)
        extracted_json = getattr(result, 'json', None)
        if extracted_json:
            return extracted_json

        # Fallback to Document.metadata or other fields if json is missing
        logger.warning(f"Firecrawl Document has no 'json' property for {url}. Result: {result}")
        return {}

        
    except Exception as e:
        # Handle credit exhaustion or other API errors
        error_msg = str(e)
        if "402" in error_msg or "credits" in error_msg.lower():
            logger.error(f"Firecrawl credit exhaustion: {error_msg}")
        else:
            logger.error(f"Firecrawl scraping error for {url}: {e}")
            
        # Return empty dict on any failure
        return {}

async def search_business_urls(business_name: str, city: str) -> dict:
    """
    Search for Yelp and social media URLs for a business using Firecrawl search.
    Returns a dict with 'yelp_url' and 'social_urls'.
    """
    try:
        query = f"{business_name} {city} yelp facebook instagram linkedin"
        logger.info(f"Firecrawl searching for business URLs: {query}")
        
        # Run search in thread
        response = await asyncio.to_thread(
            lambda: app.search(query, limit=5)
        )
        
        results = []
        if response is not None:
            if isinstance(response, dict):
                results = response.get("data", [])
            elif isinstance(response, list):
                results = response
            else:
                # Handle SearchData Pydantic object
                results = getattr(response, "web", []) or []
            
        yelp_url = None
        social_urls = []
        
        for result in results:
            if isinstance(result, dict):
                url = result.get("url", "")
            else:
                url = getattr(result, "url", "")
            if not url:
                continue
                
            if "yelp.com/biz/" in url and not yelp_url:
                yelp_url = url
                logger.info(f"Firecrawl search found Yelp URL for {business_name}: {yelp_url}")
            elif any(domain in url for domain in ["facebook.com", "instagram.com", "linkedin.com", "twitter.com", "x.com"]):
                if url not in social_urls:
                    social_urls.append(url)
                    logger.info(f"Firecrawl search found social URL for {business_name}: {url}")
                    
        return {
            "yelp_url": yelp_url,
            "social_urls": social_urls
        }
    except Exception as e:
        logger.error(f"Firecrawl search error for {business_name} in {city}: {e}")
        return {"yelp_url": None, "social_urls": []}

