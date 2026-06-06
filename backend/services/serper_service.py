"""
Serper.dev API Service for web search and Google Maps business discovery.

Provides async methods for Maps and Web search with retry logic and rate limiting.
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional

import httpx

logger = logging.getLogger(__name__)


class SerperService:
    """
    Async client for Serper.dev API.

    Handles Google Maps business search and web search with automatic
    retry logic, rate limiting, and error handling.
    """

    BASE_URL = "https://google.serper.dev"
    MAPS_ENDPOINT = f"{BASE_URL}/maps"
    SEARCH_ENDPOINT = f"{BASE_URL}/search"

    def __init__(self, api_key: str):
        """
        Initialize Serper service with API key.

        Args:
            api_key: Serper.dev API key
        """
        self.api_key = api_key
        self.last_request_time = 0.0
        self.min_delay_between_requests = 1.0  # 1 second for free tier rate limit
        logger.info("Initialized SerperService")

    async def search_maps(
        self,
        query: str,
        num_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search Google Maps for businesses without websites.

        Args:
            query: Search query (e.g., "restaurants in Los Angeles")
            num_results: Maximum number of results to return

        Returns:
            List of business dictionaries with fields:
            - name: Business name
            - address: Full address
            - phone: Phone number
            - rating: Google rating
            - position: Result position
            - place_id: Google Place ID
            Only returns businesses where website is None/empty.

        Raises:
            Exception: If search fails after all retries
        """
        logger.info(f"Maps search: '{query}' (requesting {num_results} results)")

        # Apply rate limiting
        await self._rate_limit()

        # Prepare request
        payload = {
            "q": query,
            "num": num_results
        }

        # Execute with retry logic
        response_data = await self._request_with_retry(
            endpoint=self.MAPS_ENDPOINT,
            payload=payload,
            operation_name="search_maps"
        )

        # Extract and filter results
        places = response_data.get("places", [])
        logger.info(f"Maps search: Received {len(places)} total results")

        # Filter: only businesses WITHOUT websites
        filtered_businesses = []
        for place in places:
            website = place.get("website")
            if not website or website.strip() == "":
                business = {
                    "name": place.get("title", "Unknown"),
                    "address": place.get("address", "Unknown"),
                    "phone": place.get("phoneNumber", "Not provided"),
                    "rating": place.get("rating", 0.0),
                    "position": place.get("position", 0),
                    "place_id": place.get("placeId", "")
                }
                filtered_businesses.append(business)

        logger.info(
            f"Maps search: Filtered to {len(filtered_businesses)} businesses without websites"
        )
        return filtered_businesses

    async def search_web(
        self,
        query: str,
        num_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search the web for general information.

        Useful for scraping additional business information or research.

        Args:
            query: Search query
            num_results: Maximum number of results

        Returns:
            List of search result dictionaries with:
            - title: Page title
            - link: URL
            - snippet: Text snippet
            - position: Result position

        Raises:
            Exception: If search fails after all retries
        """
        logger.info(f"Web search: '{query}' (requesting {num_results} results)")

        # Apply rate limiting
        await self._rate_limit()

        # Prepare request
        payload = {
            "q": query,
            "num": num_results
        }

        # Execute with retry logic
        response_data = await self._request_with_retry(
            endpoint=self.SEARCH_ENDPOINT,
            payload=payload,
            operation_name="search_web"
        )

        # Extract results
        organic_results = response_data.get("organic", [])
        logger.info(f"Web search: Received {len(organic_results)} results")

        # Format results
        formatted_results = []
        for result in organic_results:
            formatted_results.append({
                "title": result.get("title", ""),
                "link": result.get("link", ""),
                "snippet": result.get("snippet", ""),
                "position": result.get("position", 0)
            })

        return formatted_results

    async def _request_with_retry(
        self,
        endpoint: str,
        payload: Dict[str, Any],
        operation_name: str,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Execute HTTP request with exponential backoff retry logic.

        Args:
            endpoint: API endpoint URL
            payload: Request body
            operation_name: Name for logging
            max_retries: Maximum retry attempts

        Returns:
            Parsed JSON response

        Raises:
            Exception: If all retries fail
        """
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }

        for attempt in range(max_retries):
            try:
                logger.info(f"{operation_name}: Attempt {attempt + 1}/{max_retries}")

                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        endpoint,
                        json=payload,
                        headers=headers
                    )

                    # Check for specific error status codes
                    if response.status_code == 401:
                        error_msg = "Authentication failed - check API key"
                        logger.error(f"{operation_name}: {error_msg}")
                        raise Exception(error_msg)

                    if response.status_code == 429:
                        error_msg = "Rate limit exceeded"
                        logger.warning(f"{operation_name}: {error_msg}")
                        # Will retry with backoff
                        raise Exception(error_msg)

                    # Raise for other HTTP errors
                    response.raise_for_status()

                    # Parse and return JSON
                    data = response.json()
                    logger.info(f"{operation_name}: Success on attempt {attempt + 1}")
                    return data

            except httpx.TimeoutException as e:
                error_msg = f"Request timeout: {str(e)}"
                logger.warning(f"{operation_name}: {error_msg}")

                if attempt < max_retries - 1:
                    delay = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    logger.info(f"{operation_name}: Retrying in {delay}s...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"{operation_name}: All {max_retries} attempts failed")
                    raise Exception(
                        f"{operation_name} failed after {max_retries} attempts: {error_msg}"
                    )

            except httpx.HTTPStatusError as e:
                error_msg = f"HTTP {e.response.status_code}: {str(e)}"
                logger.warning(f"{operation_name}: {error_msg}")

                if attempt < max_retries - 1:
                    delay = 2 ** attempt
                    logger.info(f"{operation_name}: Retrying in {delay}s...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"{operation_name}: All {max_retries} attempts failed")
                    raise Exception(
                        f"{operation_name} failed after {max_retries} attempts: {error_msg}"
                    )

            except Exception as e:
                error_msg = str(e)
                logger.warning(f"{operation_name}: {error_msg}")

                if attempt < max_retries - 1:
                    delay = 2 ** attempt
                    logger.info(f"{operation_name}: Retrying in {delay}s...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"{operation_name}: All {max_retries} attempts failed")
                    raise Exception(
                        f"{operation_name} failed after {max_retries} attempts: {error_msg}"
                    )

        # Should never reach here
        raise Exception(f"{operation_name}: Unexpected error in retry logic")

    async def _rate_limit(self) -> None:
        """
        Enforce rate limiting between API calls.

        Ensures at least 1 second delay between requests to respect
        Serper.dev free tier limits.
        """
        import time

        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time

        if time_since_last_request < self.min_delay_between_requests:
            delay = self.min_delay_between_requests - time_since_last_request
            logger.debug(f"Rate limiting: Waiting {delay:.2f}s")
            await asyncio.sleep(delay)

        self.last_request_time = time.time()
