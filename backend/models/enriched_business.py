"""
Enriched Business model - Scraper Agent output.

This model represents business data enriched with owner information,
email addresses, social profiles, and other scraped details.
"""

from typing import Optional, List
from uuid import uuid4
from pydantic import BaseModel, Field


class EnrichedBusiness(BaseModel):
    """
    Enriched business data with owner and contact information.

    This is the output format from the Scraper Agent after enriching
    RawBusiness data with additional information from web scraping.
    Includes all fields from RawBusiness plus enriched data.

    Attributes:
        id: Unique identifier for the business record
        business_name: Name of the business
        address: Physical address of the business
        phone: Contact phone number
        website: Business website URL (if available)
        rating: Google Maps rating (if available)
        google_maps_url: Direct link to Google Maps listing (if available)
        owner_name: Name of the business owner (enriched)
        email: Business or owner email address (enriched)
        social_profiles: List of social media profile URLs (enriched)
        business_description: Description of the business (enriched)
        reviews: List of customer reviews (enriched)
    """

    # Fields from RawBusiness (composition approach)
    id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique identifier for the business record"
    )
    business_name: str = Field(
        ...,
        description="Name of the business",
        min_length=1
    )
    business_type: str = Field(
        default="unknown",
        description="Type/category of business"
    )
    address: str = Field(
        ...,
        description="Physical address of the business",
        min_length=1
    )
    phone: str = Field(
        ...,
        description="Contact phone number",
        min_length=1
    )
    website: Optional[str] = Field(
        None,
        description="Business website URL"
    )
    rating: Optional[float] = Field(
        None,
        description="Google Maps rating (0-5 scale)",
        ge=0.0,
        le=5.0
    )
    google_maps_url: Optional[str] = Field(
        None,
        description="Direct link to Google Maps listing"
    )
    city: Optional[str] = Field(
        None,
        description="City where business is located"
    )
    country: Optional[str] = Field(
        None,
        description="Country where business is located"
    )
    website_status: str = Field(
        default="none",
        description="Current website status (none/outdated/weak)"
    )

    # Enriched fields from Scraper Agent
    owner_name: Optional[str] = Field(
        None,
        description="Name of the business owner"
    )
    email: Optional[str] = Field(
        None,
        description="Business or owner email address"
    )
    social_profiles: List[str] = Field(
        default_factory=list,
        description="List of social media profile URLs"
    )
    business_description: Optional[str] = Field(
        None,
        description="Description of the business and services"
    )
    reviews: List[str] = Field(
        default_factory=list,
        description="List of customer reviews"
    )

    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "business_name": "Joe's Pizza",
                "address": "123 Main St, New York, NY 10001",
                "phone": "+1-212-555-0123",
                "website": "https://joespizza.com",
                "rating": 4.5,
                "google_maps_url": "https://maps.google.com/?cid=12345",
                "owner_name": "Joe Smith",
                "email": "joe@joespizza.com",
                "social_profiles": [
                    "https://facebook.com/joespizza",
                    "https://instagram.com/joespizza"
                ],
                "business_description": "Family-owned pizzeria serving authentic NY-style pizza since 1985",
                "reviews": [
                    "Best pizza in town!",
                    "Amazing service and great atmosphere"
                ]
            }
        }
