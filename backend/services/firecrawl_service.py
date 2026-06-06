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
    try:
        # Use Firecrawl's extract capabilities
        result = app.extract(
            urls=[url],
            prompt=prompt
        )
        
        # Detailed logging of the raw result for debugging
        logger.info(f"Firecrawl raw result for {url}: {result}")
        
        # Check for success/data
        if not result or 'data' not in result:
            logger.warning(f"Firecrawl returned no data structure for {url}. Result: {result}")
            return {}
            
        return result['data']
        
    except Exception as e:
        # Handle credit exhaustion or other API errors
        error_msg = str(e)
        if "402" in error_msg or "credits" in error_msg.lower():
            logger.error(f"Firecrawl credit exhaustion: {error_msg}")
        else:
            logger.error(f"Firecrawl scraping error for {url}: {e}")
            
        # Return empty dict on any failure
        return {}
