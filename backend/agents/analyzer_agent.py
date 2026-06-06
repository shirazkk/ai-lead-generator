"""
Analyzer Agent - Score opportunity and identify problems using Gemini AI.

This agent analyzes enriched business data to determine if they are a good
candidate for web development services, scoring the opportunity and identifying
specific problems that a website could solve.
"""

import logging
from typing import Dict, Any

from ..services import GeminiService
from ..models import EnrichedBusiness
from ..config import settings
from ..prompts import ANALYZER_PROMPT

logger = logging.getLogger(__name__)


async def analyze_lead(enriched_business: EnrichedBusiness) -> Dict[str, Any]:
    """
    Analyze enriched business data and score the opportunity.

    This function uses Gemini AI to evaluate the business and determine:
    - Opportunity score (1-10 indicating quality of the lead)
    - Specific problems the business faces without a website
    - Benefits a website would provide
    - Estimated monetary value of the opportunity

    Args:
        enriched_business: Enriched business data from Scraper Agent

    Returns:
        Dictionary containing:
        - opportunity_score: int (1-10, where 10 is highest priority)
        - identified_problem: str (specific problem identified)
        - website_benefits: str (comma-separated benefits)
        - estimated_value: str (revenue/value estimate)

    Raises:
        Does not raise exceptions - returns default low score on failure

    Example:
        >>> enriched = EnrichedBusiness(...)
        >>> analysis = await analyze_lead(enriched)
        >>> print(f"Score: {analysis['opportunity_score']}/10")
        >>> print(f"Problem: {analysis['identified_problem']}")
    """
    logger.info(f"Analyzer Agent: Analyzing '{enriched_business.business_name}'")

    try:
        # Initialize Gemini service
        gemini = GeminiService(api_key=settings.gemini_api_key)

        # Prepare business data for analysis
        business_data = _format_business_data(enriched_business)

        # Build full prompt with ANALYZER_PROMPT template
        full_prompt = ANALYZER_PROMPT.format(business_data=business_data)

        # Call Gemini AI for analysis
        logger.info(
            f"Analyzer Agent: Calling Gemini AI for '{enriched_business.business_name}'"
        )

        analysis_result = await gemini.analyze_lead(business_data={
            "name": enriched_business.business_name,
            "address": enriched_business.address,
            "phone": enriched_business.phone,
            "rating": enriched_business.rating or "N/A",
            "owner": enriched_business.owner_name or "Unknown",
            "email": enriched_business.email or "Not found",
            "socials": ", ".join(enriched_business.social_profiles) if enriched_business.social_profiles else "None",
            "description": enriched_business.business_description or "No description available"
        })

        # Validate and normalize opportunity_score
        opportunity_score = analysis_result.get("opportunity_score", 3)

        # Gemini returns 0-100, we need 1-10
        if opportunity_score > 10:
            opportunity_score = min(10, max(1, opportunity_score // 10))

        # Ensure score is within valid range
        opportunity_score = max(1, min(10, opportunity_score))

        # Extract other fields with defaults
        identified_problem = analysis_result.get(
            "identified_problem",
            "Business lacks online presence for customer discovery"
        )
        website_benefits = analysis_result.get(
            "website_benefits",
            "Online visibility, Customer engagement, Business credibility"
        )
        estimated_value = analysis_result.get(
            "estimated_value",
            "$500-1500/month potential increase"
        )

        result = {
            "opportunity_score": opportunity_score,
            "identified_problem": identified_problem,
            "website_benefits": website_benefits,
            "estimated_value": estimated_value
        }

        logger.info(
            f"Analyzer Agent: Completed analysis for '{enriched_business.business_name}' - "
            f"Score: {opportunity_score}/10"
        )

        return result

    except Exception as e:
        logger.error(
            f"Analyzer Agent failed for '{enriched_business.business_name}': {e}",
            exc_info=True
        )

        # Return default low-priority analysis (graceful degradation)
        return {
            "opportunity_score": 3,
            "identified_problem": (
                f"{enriched_business.business_name} may benefit from improved "
                "online presence, but analysis could not be completed."
            ),
            "website_benefits": (
                "Online visibility, Customer discovery, Business credibility, "
                "Contact information accessibility"
            ),
            "estimated_value": "$500-1000/month potential"
        }


def _format_business_data(business: EnrichedBusiness) -> str:
    """
    Format business data into a readable string for AI analysis.

    Args:
        business: EnrichedBusiness object with all available data

    Returns:
        Formatted string representation of business data

    Example:
        >>> formatted = _format_business_data(enriched_business)
        >>> print(formatted)
        Business Name: Joe's Pizza
        Location: Austin, TX
        ...
    """
    # Extract city from address (simple heuristic)
    address_parts = business.address.split(',')
    city = address_parts[-2].strip() if len(address_parts) >= 2 else "Unknown"

    # Build formatted string
    data_lines = [
        f"Business Name: {business.business_name}",
        f"Location: {city}",
        f"Full Address: {business.address}",
        f"Phone: {business.phone}",
        f"Rating: {business.rating if business.rating else 'No rating'}",
        f"Website Status: {'No website' if not business.website else business.website}",
    ]

    if business.owner_name:
        data_lines.append(f"Owner: {business.owner_name}")

    if business.email:
        data_lines.append(f"Email: {business.email}")

    if business.social_profiles:
        data_lines.append(f"Social Media: {len(business.social_profiles)} profiles found")
        for profile in business.social_profiles[:3]:  # Show first 3
            data_lines.append(f"  - {profile}")

    if business.business_description:
        data_lines.append(f"Description: {business.business_description}")

    return "\n".join(data_lines)


def validate_analysis_result(analysis: Dict[str, Any]) -> bool:
    """
    Validate that analysis result contains all required fields.

    Args:
        analysis: Analysis result dictionary from analyze_lead()

    Returns:
        True if valid, False otherwise

    Example:
        >>> analysis = await analyze_lead(business)
        >>> is_valid = validate_analysis_result(analysis)
    """
    required_fields = [
        "opportunity_score",
        "identified_problem",
        "website_benefits",
        "estimated_value"
    ]

    # Check all required fields exist
    if not all(field in analysis for field in required_fields):
        logger.warning("Analysis result missing required fields")
        return False

    # Validate opportunity_score is int and in range
    score = analysis.get("opportunity_score")
    if not isinstance(score, int) or score < 1 or score > 10:
        logger.warning(f"Invalid opportunity_score: {score}")
        return False

    # Validate string fields are non-empty
    for field in ["identified_problem", "website_benefits", "estimated_value"]:
        value = analysis.get(field)
        if not isinstance(value, str) or len(value.strip()) == 0:
            logger.warning(f"Invalid {field}: {value}")
            return False

    return True
