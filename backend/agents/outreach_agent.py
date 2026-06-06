"""
Outreach Agent - Generate hyper-personalized cold emails using Gemini AI.

This agent creates compelling, personalized outreach emails based on lead
analysis, using proven copywriting principles and AI-powered personalization.
"""

import logging
from typing import Dict, Any

from services.gemini_service import GeminiService
from models import Outreach
from config import settings
from prompts import OUTREACH_PROMPT

logger = logging.getLogger(__name__)


async def generate_outreach(
    lead_data: Dict[str, Any],
    analysis: Dict[str, Any],
    gemini: GeminiService = None
) -> Outreach:
    """
    Generate personalized cold email outreach for a qualified lead.

    This function uses Gemini AI with specialized copywriting prompts to
    create hyper-personalized emails that reference specific business details
    and problems identified in the analysis phase.

    Args:
        lead_data: Dictionary containing lead information:
            - business_name: Name of the business
            - owner_name: Owner's name (if available)
            - city: Business location
            - rating: Google rating
            - review_count: Number of reviews (if available)
            - address: Full address
            - phone: Contact phone
            - email: Contact email (if found)
            - description: Business description (if found)

        analysis: Dictionary containing analysis results:
            - opportunity_score: Score from 1-10
            - identified_problem: Specific problem identified
            - website_benefits: Benefits a website would provide
            - estimated_value: Monetary value estimate
        gemini: Optional GeminiService instance for dependency injection

    Returns:
        Outreach object containing:
        - lead_id: Reference to lead (from lead_data['id'] if present)
        - subject: Email subject line
        - message: Email body content
        - tone: Communication tone (default: 'friendly')

    Raises:
        Does not raise exceptions - returns fallback email on failure

    Example:
        >>> lead = {"business_name": "Joe's Pizza", "city": "Austin", ...}
        >>> analysis = {"opportunity_score": 8, "identified_problem": ..., ...}
        >>> outreach = await generate_outreach(lead, analysis)
        >>> print(outreach.subject)
        >>> print(outreach.message)
    """
    business_name = lead_data.get("business_name", "Unknown Business")
    logger.info(f"Outreach Agent: Generating email for '{business_name}'")

    try:
        # Initialize Gemini service (use injected or new instance)
        if gemini is None:
            gemini = GeminiService(api_key=settings.gemini_api_key)

        # Format business data for the prompt
        formatted_data = _format_outreach_data(lead_data, analysis)

        # Call Gemini AI for outreach generation
        logger.info(f"Outreach Agent: Calling Gemini AI for '{business_name}'")

        outreach_result = await gemini.generate_outreach(
            lead_data=lead_data,
            analysis=analysis
        )

        # Extract subject and message
        subject = outreach_result.get("subject", "").strip()
        message = outreach_result.get("message", "").strip()

        # Validate output
        if not subject or not message:
            logger.warning(
                f"Outreach Agent: Empty subject or message for '{business_name}', "
                "using fallback"
            )
            return _create_fallback_outreach(lead_data, analysis)

        # Validate message length (aim for 120-180 words, but be flexible)
        word_count = len(message.split())
        if word_count < 80 or word_count > 250:
            logger.warning(
                f"Outreach Agent: Message length {word_count} words for '{business_name}' "
                f"(target: 120-180)"
            )

        # Create Outreach object
        outreach = Outreach(
            lead_id=lead_data.get("id", "unknown"),
            subject=subject,
            message=message,
            tone="friendly",  # Default tone
            sent=False,
            sent_at=None
        )

        logger.info(
            f"Outreach Agent: Generated email for '{business_name}' - "
            f"Subject: '{subject[:50]}...', Words: {word_count}"
        )

        return outreach

    except Exception as e:
        logger.error(
            f"Outreach Agent failed for '{business_name}': {e}",
            exc_info=True
        )

        # Return fallback email (graceful degradation)
        return _create_fallback_outreach(lead_data, analysis)


def _format_outreach_data(
    lead_data: Dict[str, Any],
    analysis: Dict[str, Any]
) -> str:
    """
    Format lead and analysis data into a structured string for AI prompt.

    Args:
        lead_data: Lead information dictionary
        analysis: Analysis results dictionary

    Returns:
        Formatted string with all relevant data for outreach generation

    Example:
        >>> formatted = _format_outreach_data(lead, analysis)
        >>> print(formatted)
        Business: Joe's Pizza
        Owner: Joe Smith
        ...
    """
    lines = [
        f"Business: {lead_data.get('business_name', 'Unknown')}",
        f"Owner: {lead_data.get('owner_name', 'Unknown')}",
        f"Location: {lead_data.get('city', 'Unknown')}",
        f"Rating: {lead_data.get('rating', 'N/A')}",
        f"Phone: {lead_data.get('phone', 'Not provided')}",
        "",
        "ANALYSIS:",
        f"Opportunity Score: {analysis.get('opportunity_score', 0)}/10",
        f"Problem: {analysis.get('identified_problem', 'Unknown')}",
        f"Benefits: {analysis.get('website_benefits', 'Unknown')}",
        f"Value: {analysis.get('estimated_value', 'Unknown')}",
    ]

    # Add optional fields if available
    if lead_data.get("email"):
        lines.insert(5, f"Email: {lead_data['email']}")

    if lead_data.get("description"):
        lines.append(f"Description: {lead_data['description']}")

    return "\n".join(lines)


def _create_fallback_outreach(
    lead_data: Dict[str, Any],
    analysis: Dict[str, Any]
) -> Outreach:
    """
    Create a generic fallback email when AI generation fails.

    This provides a safe default that still includes some personalization
    based on available lead data.

    Args:
        lead_data: Lead information dictionary
        analysis: Analysis results dictionary

    Returns:
        Outreach object with fallback email content

    Example:
        >>> outreach = _create_fallback_outreach(lead, analysis)
        >>> print(outreach.message)
    """
    business_name = lead_data.get("business_name", "your business")
    owner_name = lead_data.get("owner_name", "")
    city = lead_data.get("city", "your area")
    problem = analysis.get("identified_problem", "lack of online presence")

    # Determine greeting
    greeting = f"Hi {owner_name}" if owner_name else f"Hi there"

    # Build fallback subject
    subject = f"Quick question about {business_name}"

    # Build fallback message
    message = f"""{greeting},

I came across {business_name} in {city} and was impressed by your presence in the local market.

I noticed {problem}, which might be limiting your business growth potential. Many similar businesses have seen significant results after establishing a professional online presence.

I specialize in helping local businesses like yours build effective websites that drive real results. Would you be open to a brief 10-minute call to discuss some specific ideas for {business_name}?

Best regards,
[Your Name]

P.S. No pressure - if the timing isn't right, I completely understand."""

    logger.info(
        f"Outreach Agent: Created fallback email for '{business_name}'"
    )

    return Outreach(
        lead_id=lead_data.get("id", "unknown"),
        subject=subject,
        message=message,
        tone="friendly",
        sent=False,
        sent_at=None
    )


def validate_outreach(outreach: Outreach) -> bool:
    """
    Validate that outreach object meets quality standards.

    Args:
        outreach: Outreach object to validate

    Returns:
        True if valid, False otherwise

    Checks:
    - Subject is not empty and under 200 chars
    - Message is not empty and between 80-300 words
    - Tone is valid

    Example:
        >>> outreach = await generate_outreach(lead, analysis)
        >>> is_valid = validate_outreach(outreach)
    """
    # Validate subject
    if not outreach.subject or len(outreach.subject) > 200:
        logger.warning("Invalid subject line")
        return False

    # Validate message
    if not outreach.message:
        logger.warning("Empty message")
        return False

    word_count = len(outreach.message.split())
    if word_count < 80 or word_count > 300:
        logger.warning(f"Message word count {word_count} outside acceptable range")
        return False

    # Validate tone
    valid_tones = {"friendly", "professional", "casual"}
    if outreach.tone not in valid_tones:
        logger.warning(f"Invalid tone: {outreach.tone}")
        return False

    return True
