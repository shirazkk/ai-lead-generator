"""
Search Router - Orchestrate lead discovery and enrichment pipeline.

This router coordinates the full lead generation workflow:
1. Discovery Agent - Find businesses without websites
2. Scraper Agent - Enrich with owner, email, socials
3. Analyzer Agent - Score opportunity and identify problems
4. Outreach Agent - Generate personalized emails
5. Save all data to Supabase
"""

import logging
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from ..agents.discovery_agent import discover_leads
from ..agents.scraper_agent import enrich_business
from ..agents.analyzer_agent import analyze_lead
from ..agents.outreach_agent import generate_outreach
from ..services.supabase_service import SupabaseService
from ..models.lead import Lead
from ..models.outreach import Outreach

logger = logging.getLogger(__name__)

# Initialize router with prefix and tags
router = APIRouter(
    prefix="/api/search",
    tags=["Search"]
)

# Initialize Supabase service
db = SupabaseService()


# Request/Response Models

class SearchRequest(BaseModel):
    """Request body for lead search endpoint."""
    city: str = Field(
        ...,
        description="Target city for business search",
        min_length=1,
        examples=["Los Angeles", "Austin", "Miami"]
    )
    business_type: str = Field(
        ...,
        description="Type of business to search for",
        min_length=1,
        examples=["restaurants", "salons", "gyms", "bakeries"]
    )
    count: int = Field(
        10,
        description="Number of leads to discover",
        ge=1,
        le=50
    )


class SearchStats(BaseModel):
    """Statistics for search results."""
    total: int = Field(..., description="Total number of leads found")
    high_score_count: int = Field(..., description="Number of leads with score >= 7")
    avg_score: float = Field(..., description="Average opportunity score")


class SearchResponse(BaseModel):
    """Response body for lead search endpoint."""
    success: bool = Field(..., description="Whether the search was successful")
    leads: List[Lead] = Field(..., description="List of discovered and qualified leads")
    stats: SearchStats = Field(..., description="Summary statistics")
    error: Dict[str, Any] | None = Field(None, description="Error details if failed")


# Endpoints

@router.post(
    "",
    response_model=SearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Discover and qualify leads",
    description="Orchestrates the full lead generation pipeline from discovery to outreach"
)
async def search_leads(request: SearchRequest) -> SearchResponse:
    """
    Execute full lead discovery and qualification pipeline.

    This endpoint orchestrates all 4 agents in sequence:
    1. DiscoveryAgent - Search Google Maps for businesses without websites
    2. ScraperAgent - Enrich each business with owner, email, socials
    3. AnalyzerAgent - Score opportunity and identify problems
    4. OutreachAgent - Generate personalized outreach emails
    5. Save all leads and outreach to Supabase

    Args:
        request: Search parameters (city, business_type, count)

    Returns:
        SearchResponse with discovered leads and statistics

    Raises:
        HTTPException: If pipeline fails or no leads found
    """
    logger.info(
        f"Starting lead search: city={request.city}, "
        f"type={request.business_type}, count={request.count}"
    )

    try:
        # PHASE 1: Discovery Agent - Find businesses without websites
        logger.info("PHASE 1: Running Discovery Agent")
        raw_businesses = await discover_leads(
            city=request.city,
            business_type=request.business_type,
            count=request.count
        )

        if not raw_businesses:
            logger.warning("No businesses found by Discovery Agent")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "type": "NO_LEADS_FOUND",
                    "message": f"No {request.business_type} without websites found in {request.city}",
                    "details": {
                        "city": request.city,
                        "business_type": request.business_type,
                        "requested_count": request.count
                    }
                }
            )

        logger.info(f"Discovery Agent found {len(raw_businesses)} raw businesses")

        # PHASE 2-5: Process each business through the pipeline
        leads: List[Lead] = []
        outreach_records: List[Outreach] = []

        for idx, raw_business in enumerate(raw_businesses, 1):
            try:
                logger.info(
                    f"Processing business {idx}/{len(raw_businesses)}: "
                    f"{raw_business.business_name}"
                )

                # PHASE 2: Scraper Agent - Enrich business data
                logger.info(f"  PHASE 2: Enriching '{raw_business.business_name}'")
                enriched_business = await enrich_business(raw_business)

                # PHASE 3: Analyzer Agent - Score opportunity
                logger.info(f"  PHASE 3: Analyzing '{enriched_business.business_name}'")
                analysis = await analyze_lead(enriched_business)

                # Create Lead object from enriched data + analysis
                lead = Lead(
                    business_name=enriched_business.business_name,
                    business_type=enriched_business.business_type,
                    owner_name=enriched_business.owner_name,
                    email=enriched_business.email,
                    phone=enriched_business.phone,
                    address=enriched_business.address,
                    city=enriched_business.city if enriched_business.city and enriched_business.city != "Unknown" else request.city,
                    country=enriched_business.country or "USA",
                    google_maps_url=enriched_business.google_maps_url,
                    social_profiles=enriched_business.social_profiles,
                    website_status=enriched_business.website_status,
                    business_description=enriched_business.business_description,
                    opportunity_score=analysis["opportunity_score"],
                    identified_problem=analysis["identified_problem"],
                    website_benefits=analysis["website_benefits"].split(", ") if isinstance(analysis["website_benefits"], str) else analysis["website_benefits"],
                    estimated_value=analysis["estimated_value"]
                )

                # PHASE 4: Outreach Agent - Generate personalized email
                logger.info(f"  PHASE 4: Generating outreach for '{lead.business_name}'")

                # Prepare lead data dict for outreach agent
                lead_data = {
                    "id": lead.id,
                    "business_name": lead.business_name,
                    "owner_name": lead.owner_name,
                    "city": lead.city,
                    "rating": getattr(enriched_business, "rating", None),
                    "review_count": getattr(enriched_business, "review_count", None),
                    "address": lead.address,
                    "phone": lead.phone,
                    "email": lead.email,
                    "description": lead.business_description
                }

                outreach = await generate_outreach(lead_data, analysis)
                # Update outreach with correct lead_id
                outreach.lead_id = lead.id

                # PHASE 5: Save to Supabase
                logger.info(f"  PHASE 5: Saving '{lead.business_name}' to database")

                # Convert Lead to dict for database insertion
                lead_dict = lead.model_dump()
                await db.create_lead(lead_dict)

                # Convert Outreach to dict for database insertion
                outreach_dict = outreach.model_dump()
                logger.info(f"Attempting to save outreach to Supabase: {outreach_dict}")
                
                # Capture result for debugging
                saved_outreach = await db.create_outreach(outreach_dict)
                logger.info(f"Outreach save successful! Saved record ID: {saved_outreach.get('id')}")
                
                leads.append(lead)
                outreach_records.append(outreach)

                logger.info(
                    f"Successfully processed '{lead.business_name}' "
                    f"(score: {lead.opportunity_score}/10)"
                )

            except Exception as e:
                logger.error(
                    f"Failed to process business '{raw_business.business_name}': {e}",
                    exc_info=True
                )
                # Continue with next business instead of failing entire pipeline
                continue

        # Check if we have any successfully processed leads
        if not leads:
            logger.error("All businesses failed processing")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "type": "PROCESSING_FAILED",
                    "message": "Failed to process any businesses through the pipeline",
                    "details": {
                        "raw_businesses_found": len(raw_businesses),
                        "successfully_processed": 0
                    }
                }
            )

        # Calculate statistics
        high_score_count = sum(1 for lead in leads if lead.opportunity_score >= 7)
        avg_score = sum(lead.opportunity_score for lead in leads) / len(leads)

        stats = SearchStats(
            total=len(leads),
            high_score_count=high_score_count,
            avg_score=round(avg_score, 2)
        )

        logger.info(
            f"Search completed successfully: {stats.total} leads, "
            f"{stats.high_score_count} high-value, avg score {stats.avg_score}"
        )

        return SearchResponse(
            success=True,
            leads=leads,
            stats=stats,
            error=None
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise

    except Exception as e:
        logger.error(f"Unexpected error in search pipeline: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "type": "INTERNAL_ERROR",
                "message": "An unexpected error occurred during lead search",
                "details": {
                    "error": str(e),
                    "city": request.city,
                    "business_type": request.business_type
                }
            }
        )
