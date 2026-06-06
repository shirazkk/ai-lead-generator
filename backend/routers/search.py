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
import asyncio
import uuid
from typing import Dict, Any, List, Optional, Tuple
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

# Define semaphore for rate limiting
CONCURRENCY_LIMIT = 3
processing_semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)

from agents.discovery_agent import discover_businesses
from agents.scraper_agent import enrich_business
from agents.analyzer_agent import analyze_lead
from agents.outreach_agent import generate_outreach
from services.supabase_service import SupabaseService
from services.gemini_service import GeminiService
from services.job_store import initialize_job, update_job_status, get_job_status
from models.lead import Lead
from models.outreach import Outreach
from config import settings
from models import RawBusiness

logger = logging.getLogger(__name__)

# Initialize router with prefix and tags
router = APIRouter(
    prefix="/api/search",
    tags=["Search"]
)

# Initialize services
db = SupabaseService()
gemini = GeminiService(api_key=settings.gemini_api_key)


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
    job_id: str = Field(..., description="Unique job identifier for progress tracking")
    leads: Optional[List[Lead]] = Field(None, description="List of discovered and qualified leads (populated on completion)")
    stats: Optional[SearchStats] = Field(None, description="Summary statistics (populated on completion)")
    error: Dict[str, Any] | None = Field(None, description="Error details if failed")


async def _process_single_business(
    raw_business: RawBusiness,
    city: str,
    job_id: str
) -> Optional[Tuple[Lead, Outreach]]:
    """Helper to process a single business through the pipeline."""
    async with processing_semaphore:
        try:
            # PHASE 2: Scraper Agent - Enrich business data
            enriched_business = await enrich_business(raw_business)

            # PHASE 3: Analyzer Agent - Score opportunity
            analysis = await analyze_lead(enriched_business, gemini=gemini)

            # Create Lead object
            lead = Lead(
                business_name=enriched_business.business_name,
                business_type=enriched_business.business_type,
                owner_name=enriched_business.owner_name,
                email=enriched_business.email,
                phone=enriched_business.phone,
                address=enriched_business.address,
                city=enriched_business.city if enriched_business.city and enriched_business.city != "Unknown" else city,
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

            outreach = await generate_outreach(lead_data, analysis, gemini=gemini)
            outreach.lead_id = lead.id

            # PHASE 5: Save to Supabase
            await db.create_lead(lead.model_dump())
            await db.create_outreach(outreach.model_dump())
            
            # Update progress
            status_data = get_job_status(job_id)
            if status_data:
                new_processed = status_data["processed"] + 1
                new_progress = int((new_processed / status_data["total_businesses"]) * 100)
                await update_job_status(job_id, {
                    "processed": new_processed,
                    "progress": new_progress,
                    "status": "completed" if new_processed == status_data["total_businesses"] else "running"
                })

            return lead, outreach
        except Exception as e:
            logger.error(f"Failed to process '{raw_business.business_name}': {e}")
            return None

@router.post(
    "",
    response_model=SearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Discover and qualify leads",
    description="Orchestrates the full lead generation pipeline from discovery to outreach"
)
async def search_leads(request: SearchRequest) -> SearchResponse:
    logger.info(
        f"Starting lead search: city={request.city}, "
        f"type={request.business_type}, count={request.count}"
    )

    try:
        # PHASE 1: Discovery Agent
        logger.info("PHASE 1: Running Discovery Agent")
        raw_businesses = await discover_businesses(
            city=request.city,
            business_type=request.business_type,
            count=request.count
        )

        if not raw_businesses:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No leads found")

        # Initialize job tracking
        job_id = str(uuid.uuid4())
        initialize_job(job_id, len(raw_businesses))
        logger.info(f"Initialized job tracking: {job_id}")

        # PHASE 2-5: Parallel processing
        logger.info("Starting parallel pipeline processing")
        tasks = [
            _process_single_business(raw_business, request.city, job_id)
            for raw_business in raw_businesses
        ]

        results = await asyncio.gather(*tasks)

        # Collect results
        leads: List[Lead] = []
        outreach_records: List[Outreach] = []
        for result in results:
            if result:
                leads.append(result[0])
                outreach_records.append(result[1])

        # Final stats
        high_score_count = sum(1 for lead in leads if lead.opportunity_score >= 7)
        avg_score = sum(lead.opportunity_score for lead in leads) / len(leads) if leads else 0

        return SearchResponse(
            success=True,
            job_id=job_id,
            leads=leads,
            stats=SearchStats(total=len(leads), high_score_count=high_score_count, avg_score=round(avg_score, 2))
        )

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
