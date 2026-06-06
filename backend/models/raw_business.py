"""
Raw Business model - Discovery Agent output.

This model represents the initial business data collected from Google Maps
via the Serper API by the Discovery Agent.
"""

from typing import Optional, List
from uuid import uuid4
from pydantic import BaseModel, Field


class RawBusiness(BaseModel):
    """
    Raw business data from Google Maps search results.

    This is the output format from the Discovery Agent after searching
    for businesses using Serper Maps API. Contains basic business
    information without enrichment.

    Attributes:
        id: Unique identifier for the business record
        business_name: Name of the business
        address: Physical address of the business
        phone: Contact phone number
        website: Business website URL (if available)
        rating: Google Maps rating (if available)
        google_maps_url: Direct link to Google Maps listing (if available)
    """

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
    place_id: Optional[str] = Field(
        None,
        description="Google Places API ID"
    )
    country: Optional[str] = Field(
        None,
        description="Country where business is located"
    )
    yelp_url: Optional[str] = Field(
        None,
        description="Direct link to Yelp listing"
    )
    social_urls: List[str] = Field(
        default_factory=list,
        description="List of social media URLs"
    )
    website_status: str = Field(
        default="none",
        description="Current website status (none/outdated/weak)"
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
                "google_maps_url": "https://maps.google.com/?cid=12345"
            }
        }
