"""
Lead model - Complete qualified lead data.

This model represents a fully qualified lead with business information,
contact details, opportunity scoring, and identified problems/solutions.
"""

from typing import List, Optional
from datetime import datetime, timezone
from uuid import uuid4
from pydantic import BaseModel, Field, field_validator


class Lead(BaseModel):
    """
    Complete lead model with qualification and scoring.

    This is the final output from the Lead Qualifier Agent after analyzing
    enriched business data and determining opportunity value. Contains all
    information needed for outreach and CRM integration.

    Attributes:
        id: Unique identifier for the lead
        business_name: Name of the business
        business_type: Type/category of business
        owner_name: Name of the business owner
        email: Contact email address
        phone: Contact phone number
        address: Physical address
        city: City location
        country: Country location
        google_maps_url: Link to Google Maps listing
        social_profiles: List of social media URLs
        website_status: Current website status (none/outdated/weak)
        business_description: Description of the business
        opportunity_score: Score from 1-10 indicating opportunity value
        identified_problem: The main problem/pain point identified
        website_benefits: List of benefits a website would provide
        estimated_value: Estimated monetary value of the opportunity
        created_at: Timestamp when lead was created
    """

    id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique identifier for the lead"
    )
    business_name: str = Field(
        ...,
        description="Name of the business",
        min_length=1
    )
    business_type: str = Field(
        ...,
        description="Type or category of business (e.g., restaurant, retail, service)",
        min_length=1
    )
    owner_name: Optional[str] = Field(
        None,
        description="Name of the business owner or primary contact"
    )
    email: Optional[str] = Field(
        None,
        description="Contact email address"
    )
    phone: str = Field(
        ...,
        description="Contact phone number",
        min_length=1
    )
    address: str = Field(
        ...,
        description="Physical address of the business",
        min_length=1
    )
    city: str = Field(
        ...,
        description="City where business is located",
        min_length=1
    )
    country: str = Field(
        ...,
        description="Country where business is located",
        min_length=1
    )
    google_maps_url: Optional[str] = Field(
        None,
        description="Direct link to Google Maps listing"
    )
    social_profiles: List[str] = Field(
        default_factory=list,
        description="List of social media profile URLs"
    )
    website_status: str = Field(
        ...,
        description="Current website status: 'none' | 'outdated' | 'weak'"
    )
    business_description: Optional[str] = Field(
        None,
        description="Description of the business and what it offers"
    )
    opportunity_score: int = Field(
        ...,
        description="Opportunity score from 1-10 (1=low, 10=high)",
        ge=1,
        le=10
    )
    identified_problem: str = Field(
        ...,
        description="The main problem or pain point identified",
        min_length=1
    )
    website_benefits: List[str] = Field(
        default_factory=list,
        description="List of specific benefits a website would provide"
    )
    estimated_value: Optional[str] = Field(
        None,
        description="Estimated monetary value of the opportunity (e.g., '$5,000-$10,000')"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the lead was created"
    )

    @field_validator("opportunity_score")
    @classmethod
    def validate_opportunity_score(cls, v: int) -> int:
        """
        Validate opportunity score is between 1 and 10.

        Args:
            v: The opportunity score value

        Returns:
            The validated opportunity score

        Raises:
            ValueError: If score is not between 1 and 10
        """
        if v < 1 or v > 10:
            raise ValueError("opportunity_score must be between 1 and 10")
        return v

    @field_validator("website_status")
    @classmethod
    def validate_website_status(cls, v: str) -> str:
        """
        Validate website status is one of the allowed values.

        Args:
            v: The website status value

        Returns:
            The validated website status

        Raises:
            ValueError: If status is not 'none', 'outdated', or 'weak'
        """
        allowed_statuses = {"none", "outdated", "weak"}
        if v not in allowed_statuses:
            raise ValueError(
                f"website_status must be one of {allowed_statuses}, got '{v}'"
            )
        return v

    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "business_name": "Joe's Pizza",
                "business_type": "Restaurant",
                "owner_name": "Joe Smith",
                "email": "joe@joespizza.com",
                "phone": "+1-212-555-0123",
                "address": "123 Main St",
                "city": "New York",
                "country": "USA",
                "google_maps_url": "https://maps.google.com/?cid=12345",
                "social_profiles": [
                    "https://facebook.com/joespizza",
                    "https://instagram.com/joespizza"
                ],
                "website_status": "none",
                "business_description": "Family-owned pizzeria serving authentic NY-style pizza",
                "opportunity_score": 8,
                "identified_problem": "No online presence limits customer discovery and ordering",
                "website_benefits": [
                    "Online ordering system",
                    "Menu showcase with photos",
                    "Customer reviews display",
                    "Delivery tracking"
                ],
                "estimated_value": "$5,000-$8,000",
                "created_at": "2026-06-06T06:53:22.692Z"
            }
        }
