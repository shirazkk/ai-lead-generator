"""
Gemini AI Service for lead analysis and outreach generation.

Uses Google Gemini 2.0 Flash with structured JSON output for reliable parsing.
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from typing_extensions import TypedDict

import google.generativeai as genai
from google.generativeai.types import GenerationConfig

logger = logging.getLogger(__name__)


# Type definitions for structured outputs
class LeadAnalysisResult(TypedDict):
    """Structured output schema for lead analysis."""
    opportunity_score: int  # 0-100
    identified_problem: str
    website_benefits: str
    estimated_value: str


class OutreachResult(TypedDict):
    """Structured output schema for outreach generation."""
    subject: str
    message: str


class GeminiService:
    """
    Async client for Google Gemini 2.0 Flash API.

    Provides structured JSON output for lead analysis and outreach generation
    with automatic retry logic and error handling.
    """

    def __init__(self, api_key: str):
        """
        Initialize Gemini service with API key.

        Args:
            api_key: Google Gemini API key
        """
        self.api_key = api_key
        genai.configure(api_key=api_key)
        self.model_name = "gemini-3-flash-preview"
        logger.info(f"Initialized GeminiService with model {self.model_name}")

    async def analyze_lead(self, business_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a business lead and return structured assessment.

        Args:
            business_data: Dictionary containing business info (name, address, phone, etc.)

        Returns:
            Dictionary with analysis results:
            - opportunity_score: int (0-100)
            - identified_problem: str
            - website_benefits: str
            - estimated_value: str

        Raises:
            Exception: If analysis fails after all retries
        """
        # Define JSON schema for structured output
        analysis_schema = {
            "type": "object",
            "properties": {
                "opportunity_score": {
                    "type": "integer",
                    "description": "Lead quality score from 0-100"
                },
                "identified_problem": {
                    "type": "string",
                    "description": "Main business problem identified"
                },
                "website_benefits": {
                    "type": "string",
                    "description": "How a website would help this business"
                },
                "estimated_value": {
                    "type": "string",
                    "description": "Potential value/revenue estimate"
                }
            },
            "required": ["opportunity_score", "identified_problem", "website_benefits", "estimated_value"]
        }

        # Short focused prompt (detailed prompts will be in backend/prompts/)
        prompt = f"""Analyze this business as a potential web development lead:

Business: {business_data.get('name', 'Unknown')}
Location: {business_data.get('address', 'Unknown')}
Phone: {business_data.get('phone', 'Not provided')}
Rating: {business_data.get('rating', 'N/A')}

Assess opportunity score, identify problems, explain website benefits, and estimate value."""

        generation_config = GenerationConfig(
            response_mime_type="application/json",
            response_schema=analysis_schema
        )

        return await self._generate_with_retry(
            prompt=prompt,
            generation_config=generation_config,
            operation_name="analyze_lead"
        )

    async def generate_outreach(
        self,
        lead_data: Dict[str, Any],
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate personalized outreach email for a lead.

        Args:
            lead_data: Business information
            analysis: Previous analysis results from analyze_lead()

        Returns:
            Dictionary with:
            - subject: Email subject line
            - message: Email body content

        Raises:
            Exception: If generation fails after all retries
        """
        # Define JSON schema for structured output
        outreach_schema = {
            "type": "object",
            "properties": {
                "subject": {
                    "type": "string",
                    "description": "Compelling email subject line"
                },
                "message": {
                    "type": "string",
                    "description": "Personalized email body"
                }
            },
            "required": ["subject", "message"]
        }

        # Short focused prompt
        prompt = f"""Generate personalized outreach email for:

Business: {lead_data.get('name', 'Unknown')}
Problem: {analysis.get('identified_problem', 'Unknown')}
Benefits: {analysis.get('website_benefits', 'Unknown')}
Value: {analysis.get('estimated_value', 'Unknown')}

Create compelling subject and message."""

        generation_config = GenerationConfig(
            response_mime_type="application/json",
            response_schema=outreach_schema
        )

        return await self._generate_with_retry(
            prompt=prompt,
            generation_config=generation_config,
            operation_name="generate_outreach"
        )

    async def _generate_with_retry(
        self,
        prompt: str,
        generation_config: GenerationConfig,
        operation_name: str,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Generate content with exponential backoff retry logic.

        Args:
            prompt: Input prompt
            generation_config: Generation configuration with JSON schema
            operation_name: Name of operation for logging
            max_retries: Maximum retry attempts

        Returns:
            Parsed JSON response

        Raises:
            Exception: If all retries fail
        """
        model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config=generation_config
        )

        for attempt in range(max_retries):
            try:
                logger.info(f"{operation_name}: Attempt {attempt + 1}/{max_retries}")

                # Generate content
                response = await asyncio.to_thread(
                    model.generate_content,
                    prompt
                )

                # Log token usage
                if hasattr(response, 'usage_metadata') and response.usage_metadata:
                    usage = response.usage_metadata
                    logger.info(
                        f"{operation_name}: Tokens used - "
                        f"Prompt: {usage.prompt_token_count}, "
                        f"Response: {usage.candidates_token_count}, "
                        f"Total: {usage.total_token_count}"
                    )

                # Parse JSON response
                import json
                result = json.loads(response.text)

                logger.info(f"{operation_name}: Success on attempt {attempt + 1}")
                return result

            except Exception as e:
                error_msg = str(e)
                logger.warning(
                    f"{operation_name}: Attempt {attempt + 1} failed: {error_msg}"
                )

                # Check if we should retry
                if attempt < max_retries - 1:
                    # Exponential backoff: 1s, 2s, 4s
                    delay = 2 ** attempt
                    logger.info(f"{operation_name}: Retrying in {delay}s...")
                    await asyncio.sleep(delay)
                else:
                    # All retries exhausted
                    logger.error(
                        f"{operation_name}: All {max_retries} attempts failed"
                    )
                    raise Exception(
                        f"{operation_name} failed after {max_retries} attempts: {error_msg}"
                    )

        # Should never reach here, but for type safety
        raise Exception(f"{operation_name}: Unexpected error in retry logic")
