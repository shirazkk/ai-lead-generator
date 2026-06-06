"""
Scraper Agent - Enrich business data with owner, email, socials, and description.

This agent takes raw business data and enriches it by scraping the web for
additional information like owner names, email addresses, social profiles,
and business descriptions.
"""

import logging
import re
import asyncio
from typing import Optional, List

from ..services import SerperService
from ..models import RawBusiness, EnrichedBusiness
from ..config import settings

logger = logging.getLogger(__name__)


# Regex patterns for data extraction
EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')

# Owner name patterns (case-insensitive)
OWNER_PATTERNS = [
    re.compile(r'owner[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', re.IGNORECASE),
    re.compile(r'founded by[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', re.IGNORECASE),
    re.compile(r'by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)(?:\s+and|\s+&|\s*,|\s*$)', re.IGNORECASE),
    re.compile(r'proprietor[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', re.IGNORECASE),
]

# Social media URL patterns
SOCIAL_PATTERNS = {
    'facebook': re.compile(r'https?://(?:www\.)?facebook\.com/[A-Za-z0-9._-]+', re.IGNORECASE),
    'instagram': re.compile(r'https?://(?:www\.)?instagram\.com/[A-Za-z0-9._-]+', re.IGNORECASE),
    'twitter': re.compile(r'https?://(?:www\.)?(?:twitter|x)\.com/[A-Za-z0-9._-]+', re.IGNORECASE),
    'linkedin': re.compile(r'https?://(?:www\.)?linkedin\.com/(?:in|company)/[A-Za-z0-9._-]+', re.IGNORECASE),
}


async def enrich_business(raw_business: RawBusiness) -> EnrichedBusiness:
    """
    Enrich raw business data with owner info, email, socials, and description.

    This function performs web searches to find additional information about
    the business that wasn't available in the initial Maps discovery.

    Args:
        raw_business: Basic business data from Discovery Agent

    Returns:
        EnrichedBusiness object with all original fields plus:
        - owner_name: Business owner's name (if found)
        - email: Contact email address (if found)
        - social_profiles: List of social media URLs
        - business_description: Description of business services
        - reviews: Customer reviews (if found)

    Raises:
        Does not raise exceptions - returns partial data if enrichment fails

    Example:
        >>> raw = RawBusiness(
        ...     business_name="Joe's Pizza",
        ...     address="123 Main St, Austin, TX",
        ...     phone="512-555-0123",
        ...     rating=4.5
        ... )
        >>> enriched = await enrich_business(raw)
        >>> print(enriched.email, enriched.owner_name)
    """
    logger.info(f"Scraper Agent: Enriching '{raw_business.business_name}'")

    try:
        # Initialize Serper service
        serper = SerperService(api_key=settings.serper_api_key)

        # Extract city and country from address for better search context
        city = _extract_city_from_address(raw_business.address)
        country = _extract_country_from_address(raw_business.address)

        # Perform web search for owner and contact info
        search_query = f"{raw_business.business_name} {city} owner email contact"
        logger.info(f"Web search query: '{search_query}'")

        # Rate limiting - 1 second delay
        await asyncio.sleep(1.0)

        search_results = await serper.search_web(query=search_query, num_results=5)

        # Extract enriched data from search results
        owner_name = _extract_owner_name(search_results)
        email = _extract_email(search_results)
        social_profiles = _extract_social_profiles(search_results)
        description = _extract_description(search_results, raw_business.business_name)

        # Log what we found
        logger.info(
            f"Scraper Agent: Enriched '{raw_business.business_name}' - "
            f"Owner: {owner_name or 'Not found'}, "
            f"Email: {email or 'Not found'}, "
            f"Socials: {len(social_profiles)}, "
            f"Description: {'Found' if description else 'Not found'}, "
            f"Country: {country}"
        )

        # Create EnrichedBusiness with all data
        enriched = EnrichedBusiness(
            # Copy all fields from RawBusiness
            id=raw_business.id,
            business_name=raw_business.business_name,
            business_type=raw_business.business_type,
            address=raw_business.address,
            phone=raw_business.phone,
            website=raw_business.website,
            rating=raw_business.rating,
            google_maps_url=raw_business.google_maps_url,
            website_status=raw_business.website_status,
            # Add city and country
            city=city or "Unknown",
            country=country or "Unknown",
            # Add enriched fields
            owner_name=owner_name,
            email=email,
            social_profiles=social_profiles,
            business_description=description,
            reviews=[]  # Reviews can be added in future enhancement
        )

        return enriched

    except Exception as e:
        logger.error(
            f"Scraper Agent failed for '{raw_business.business_name}': {e}",
            exc_info=True
        )

        # Return EnrichedBusiness with original data only (graceful degradation)
        return EnrichedBusiness(
            id=raw_business.id,
            business_name=raw_business.business_name,
            business_type=raw_business.business_type,
            address=raw_business.address,
            phone=raw_business.phone,
            website=raw_business.website,
            rating=raw_business.rating,
            google_maps_url=raw_business.google_maps_url,
            website_status=raw_business.website_status,
            city="Unknown",
            country=_extract_country_from_address(raw_business.address) or "Unknown",
            owner_name=None,
            email=None,
            social_profiles=[],
            business_description=None,
            reviews=[]
        )


def _extract_city_from_address(address: str) -> str:
    """
    Extract city name from full address string.

    Args:
        address: Full address string (e.g., "123 Main St, Austin, TX 78701")

    Returns:
        City name or empty string if extraction fails
    """
    # Simple heuristic: city is usually between first and second comma
    parts = address.split(',')
    if len(parts) >= 2:
        return parts[-2].strip()
    return ""


def _extract_country_from_address(address: str) -> str:
    """
    Extract country name from full address string.

    Args:
        address: Full address string (e.g., "123 Main St, Austin, TX 78701, USA")

    Returns:
        Country name or empty string if extraction fails
    """
    parts = address.split(',')
    if len(parts) >= 1:
        return parts[-1].strip()
    return "Unknown"


def _extract_owner_name(search_results: List[dict]) -> Optional[str]:
    """
    Extract owner name from search results using pattern matching.

    Args:
        search_results: List of search result dictionaries with 'snippet' and 'title'

    Returns:
        Owner name if found, None otherwise
    """
    for result in search_results:
        text = f"{result.get('title', '')} {result.get('snippet', '')}"

        # Try each owner pattern
        for pattern in OWNER_PATTERNS:
            match = pattern.search(text)
            if match:
                name = match.group(1).strip()
                # Validate name (at least 2 chars, contains space for full name preferred)
                if len(name) >= 2:
                    logger.debug(f"Found owner name: {name}")
                    return name

    return None


def _extract_email(search_results: List[dict]) -> Optional[str]:
    """
    Extract email address from search results using regex.

    Args:
        search_results: List of search result dictionaries

    Returns:
        Email address if found, None otherwise
    """
    for result in search_results:
        text = f"{result.get('title', '')} {result.get('snippet', '')}"

        # Search for email pattern
        match = EMAIL_PATTERN.search(text)
        if match:
            email = match.group(0)
            # Filter out common generic/info emails that might be false positives
            if not any(word in email.lower() for word in ['example', 'test', 'sample']):
                logger.debug(f"Found email: {email}")
                return email

    return None


def _extract_social_profiles(search_results: List[dict]) -> List[str]:
    """
    Extract social media profile URLs from search results.

    Args:
        search_results: List of search result dictionaries

    Returns:
        List of social media URLs (Facebook, Instagram, Twitter, LinkedIn)
    """
    profiles: List[str] = []
    seen_urls: set = set()

    for result in search_results:
        # Check both link and snippet for social URLs
        text = f"{result.get('link', '')} {result.get('snippet', '')}"

        # Try each social pattern
        for platform, pattern in SOCIAL_PATTERNS.items():
            matches = pattern.findall(text)
            for url in matches:
                # Avoid duplicates
                if url not in seen_urls:
                    profiles.append(url)
                    seen_urls.add(url)
                    logger.debug(f"Found {platform} profile: {url}")

    return profiles


def _extract_description(search_results: List[dict], business_name: str) -> Optional[str]:
    """
    Extract business description from top search result snippet.

    Args:
        search_results: List of search result dictionaries
        business_name: Name of the business (for validation)

    Returns:
        Business description if found, None otherwise
    """
    if not search_results:
        return None

    # Use snippet from first result (most relevant)
    top_result = search_results[0]
    snippet = top_result.get('snippet', '').strip()

    # Basic validation: snippet should be substantial and mention business
    if len(snippet) >= 50 and business_name.lower() in snippet.lower():
        logger.debug(f"Found description: {snippet[:100]}...")
        return snippet

    return None
