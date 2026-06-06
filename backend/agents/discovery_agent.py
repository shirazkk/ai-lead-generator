"""
Discovery Agent - Find businesses WITHOUT websites using Serper Maps API.

This agent searches Google Maps for local businesses that lack websites,
identifying potential leads for web development services.
"""

import logging
import asyncio
from typing import List

from ..services import SerperService
from ..models import RawBusiness
from ..config import settings

logger = logging.getLogger(__name__)


async def discover_leads(
    city: str,
    business_type: str,
    count: int = 10
) -> List[RawBusiness]:
    """
    Discover businesses without websites in a specific city.

    This function searches Google Maps using Serper API and filters results
    to only include businesses that do NOT have websites, as these are
    prime candidates for web development services.

    Args:
        city: Target city for business search (e.g., "Los Angeles")
        business_type: Type of business to search for (e.g., "restaurants", "salons")
        count: Desired number of leads to discover (default: 10)
               Note: Will search for count*2 to account for filtering

    Returns:
        List of RawBusiness objects containing basic business information
        from Google Maps. Returns empty list if search fails.

    Raises:
        Does not raise exceptions - returns empty list on failure and logs errors

    Example:
        >>> leads = await discover_leads("Austin", "bakeries", count=20)
        >>> print(f"Found {len(leads)} bakeries without websites")
    """
    logger.info(
        f"Discovery Agent started: searching for {count} '{business_type}' "
        f"in {city} (requesting {count * 2} results for filtering)"
    )

    try:
        # Initialize Serper service
        serper = SerperService(api_key=settings.serper_api_key)

        # Build search query
        query = f"{business_type} in {city}"
        logger.info(f"Search query: '{query}'")

        # Apply rate limiting before search (1 second delay)
        await asyncio.sleep(1.0)

        # Execute Maps search with 2x count to account for filtering
        search_results = await serper.search_maps(
            query=query,
            num_results=count * 2
        )

        logger.info(
            f"Received {len(search_results)} total results from Serper Maps API"
        )

        # Filter: ONLY businesses WITHOUT websites
        businesses_without_websites: List[RawBusiness] = []

        for result in search_results:
            # Check if website is None or empty string
            website = result.get("website")
            if not website or website.strip() == "":
                try:
                    # Create RawBusiness object
                    raw_business = RawBusiness(
                        business_name=result.get("name", "Unknown Business"),
                        business_type=business_type,
                        address=result.get("address", "Unknown Address"),
                        phone=result.get("phone", "Not provided"),
                        website=None,  # Explicitly None for businesses without websites
                        website_status="none",
                        rating=result.get("rating"),
                        google_maps_url=_build_maps_url(result.get("place_id"))
                    )

                    businesses_without_websites.append(raw_business)

                    # Stop when we reach desired count
                    if len(businesses_without_websites) >= count:
                        break

                except Exception as e:
                    logger.warning(
                        f"Failed to create RawBusiness from result: {e}. "
                        f"Skipping business: {result.get('name', 'Unknown')}"
                    )
                    continue

        logger.info(
            f"Discovery Agent completed: Found {len(businesses_without_websites)} "
            f"businesses without websites (filtered from {len(search_results)} total)"
        )

        # Return the filtered list
        return businesses_without_websites[:count]

    except Exception as e:
        logger.error(
            f"Discovery Agent failed for '{business_type}' in {city}: {e}",
            exc_info=True
        )
        # Return empty list on failure - graceful degradation
        return []


def _build_maps_url(place_id: str | None) -> str | None:
    """
    Build Google Maps URL from place_id.

    Args:
        place_id: Google Place ID from Maps API

    Returns:
        Full Google Maps URL or None if place_id is invalid

    Example:
        >>> url = _build_maps_url("ChIJN1t_tDeuEmsRUsoyG83frY4")
        >>> print(url)
        https://www.google.com/maps/place/?q=place_id:ChIJN1t_tDeuEmsRUsoyG83frY4
    """
    if not place_id or place_id.strip() == "":
        return None

    return f"https://www.google.com/maps/place/?q=place_id:{place_id}"


async def discover_leads_batch(
    cities: List[str],
    business_type: str,
    count_per_city: int = 10
) -> dict[str, List[RawBusiness]]:
    """
    Discover leads across multiple cities in parallel.

    This is a convenience function for batch processing multiple cities
    at once, useful for broader lead generation campaigns.

    Args:
        cities: List of city names to search
        business_type: Type of business to search for
        count_per_city: Number of leads to discover per city

    Returns:
        Dictionary mapping city names to lists of discovered businesses

    Example:
        >>> results = await discover_leads_batch(
        ...     cities=["Austin", "Dallas", "Houston"],
        ...     business_type="restaurants",
        ...     count_per_city=15
        ... )
        >>> for city, leads in results.items():
        ...     print(f"{city}: {len(leads)} leads")
    """
    logger.info(
        f"Batch Discovery: Searching {len(cities)} cities for '{business_type}'"
    )

    # Create tasks for parallel execution
    tasks = [
        discover_leads(city=city, business_type=business_type, count=count_per_city)
        for city in cities
    ]

    # Execute all searches in parallel
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Build result dictionary
    city_results: dict[str, List[RawBusiness]] = {}

    for city, result in zip(cities, results):
        if isinstance(result, Exception):
            logger.error(f"Batch Discovery: {city} failed with error: {result}")
            city_results[city] = []
        else:
            # Type narrowing: result is List[RawBusiness] here
            leads_list: List[RawBusiness] = result
            city_results[city] = leads_list
            logger.info(f"Batch Discovery: {city} returned {len(leads_list)} leads")

    total_leads = sum(len(leads) for leads in city_results.values())
    logger.info(
        f"Batch Discovery completed: {total_leads} total leads across {len(cities)} cities"
    )

    return city_results
