"""
Leads Router - CRUD operations for lead management.

This router provides endpoints for retrieving, filtering, and managing
leads stored in the database.
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel, Field

from ..services.supabase_service import SupabaseService
from ..models.lead import Lead
from ..models.outreach import Outreach

logger = logging.getLogger(__name__)

# Initialize router with prefix and tags
router = APIRouter(
    prefix="/api/leads",
    tags=["Leads"]
)

# Initialize Supabase service
db = SupabaseService()


# Response Models

class LeadWithOutreach(BaseModel):
    """Lead with associated outreach email."""
    lead: Lead
    outreach: Optional[Outreach] = None


class LeadsListResponse(BaseModel):
    """Response for list leads endpoint."""
    success: bool = Field(..., description="Whether the request was successful")
    data: List[Lead] = Field(..., description="List of leads")
    total: int = Field(..., description="Total number of leads returned")
    error: Optional[Dict[str, Any]] = Field(None, description="Error details if failed")


class LeadDetailResponse(BaseModel):
    """Response for single lead endpoint."""
    success: bool = Field(..., description="Whether the request was successful")
    data: Optional[LeadWithOutreach] = Field(None, description="Lead with outreach data")
    error: Optional[Dict[str, Any]] = Field(None, description="Error details if failed")


class DeleteLeadResponse(BaseModel):
    """Response for delete lead endpoint."""
    success: bool = Field(..., description="Whether the deletion was successful")
    message: str = Field(..., description="Confirmation message")
    error: Optional[Dict[str, Any]] = Field(None, description="Error details if failed")


# Endpoints

@router.get(
    "",
    response_model=LeadsListResponse,
    status_code=status.HTTP_200_OK,
    summary="List leads with filters",
    description="Retrieve paginated list of leads with optional filtering by city and score range"
)
async def list_leads(
    limit: int = Query(50, ge=1, le=100, description="Maximum number of leads to return"),
    offset: int = Query(0, ge=0, description="Number of leads to skip for pagination"),
    city: Optional[str] = Query(None, description="Filter by city (exact match)"),
    min_score: Optional[int] = Query(None, ge=1, le=10, description="Minimum opportunity score"),
    max_score: Optional[int] = Query(None, ge=1, le=10, description="Maximum opportunity score")
) -> LeadsListResponse:
    """
    Get paginated list of leads with optional filters.

    Supports filtering by:
    - city: Exact match on city name
    - min_score: Minimum opportunity score (1-10)
    - max_score: Maximum opportunity score (1-10)

    Args:
        limit: Maximum number of records (1-100, default 50)
        offset: Number of records to skip (default 0)
        city: Optional city filter
        min_score: Optional minimum score filter
        max_score: Optional maximum score filter

    Returns:
        LeadsListResponse with list of leads and count

    Raises:
        HTTPException: If database query fails
    """
    logger.info(
        f"Fetching leads: limit={limit}, offset={offset}, "
        f"city={city}, min_score={min_score}, max_score={max_score}"
    )

    try:
        # Build filters dictionary
        filters = {}
        if city:
            filters["city"] = city
        if min_score is not None:
            filters["min_score"] = min_score
        if max_score is not None:
            filters["max_score"] = max_score

        # Query database
        lead_dicts = await db.get_leads(
            limit=limit,
            offset=offset,
            filters=filters if filters else None
        )

        # Convert to Lead models
        leads = [Lead(**lead_dict) for lead_dict in lead_dicts]

        logger.info(f"Successfully retrieved {len(leads)} leads")

        return LeadsListResponse(
            success=True,
            data=leads,
            total=len(leads),
            error=None
        )

    except Exception as e:
        logger.error(f"Failed to fetch leads: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "type": "DATABASE_ERROR",
                "message": "Failed to retrieve leads from database",
                "details": {"error": str(e)}
            }
        )


@router.get(
    "/{lead_id}",
    response_model=LeadDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get single lead with outreach",
    description="Retrieve detailed information for a specific lead including associated outreach"
)
async def get_lead(lead_id: str) -> LeadDetailResponse:
    """
    Get single lead by ID with associated outreach email.

    Args:
        lead_id: UUID of the lead to retrieve

    Returns:
        LeadDetailResponse with lead and outreach data

    Raises:
        HTTPException: If lead not found or database error
    """
    logger.info(f"Fetching lead: {lead_id}")

    try:
        # Fetch lead from database
        lead_dict = await db.get_lead(lead_id)

        if not lead_dict:
            logger.warning(f"Lead not found: {lead_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "type": "LEAD_NOT_FOUND",
                    "message": f"Lead with ID '{lead_id}' not found",
                    "details": {"lead_id": lead_id}
                }
            )

        # Convert to Lead model
        lead = Lead(**lead_dict)

        # Fetch associated outreach
        outreach_dict = await db.get_outreach_by_lead(lead_id)
        outreach = Outreach(**outreach_dict) if outreach_dict else None

        logger.info(
            f"Successfully retrieved lead '{lead.business_name}' "
            f"(outreach: {'found' if outreach else 'not found'})"
        )

        return LeadDetailResponse(
            success=True,
            data=LeadWithOutreach(lead=lead, outreach=outreach),
            error=None
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise

    except Exception as e:
        logger.error(f"Failed to fetch lead {lead_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "type": "DATABASE_ERROR",
                "message": "Failed to retrieve lead from database",
                "details": {"error": str(e), "lead_id": lead_id}
            }
        )


@router.delete(
    "/{lead_id}",
    response_model=DeleteLeadResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete lead",
    description="Delete a lead and its associated outreach records (cascading delete)"
)
async def delete_lead(lead_id: str) -> DeleteLeadResponse:
    """
    Delete a lead by ID.

    This operation cascades to associated outreach records. The lead
    and all related data will be permanently removed from the database.

    Args:
        lead_id: UUID of the lead to delete

    Returns:
        DeleteLeadResponse with confirmation message

    Raises:
        HTTPException: If lead not found or database error
    """
    logger.info(f"Deleting lead: {lead_id}")

    try:
        # Check if lead exists first
        lead_dict = await db.get_lead(lead_id)

        if not lead_dict:
            logger.warning(f"Lead not found for deletion: {lead_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "type": "LEAD_NOT_FOUND",
                    "message": f"Lead with ID '{lead_id}' not found",
                    "details": {"lead_id": lead_id}
                }
            )

        business_name = lead_dict.get("business_name", "Unknown")

        # Perform deletion (cascades to outreach)
        deleted = await db.delete_lead(lead_id)

        if not deleted:
            logger.error(f"Delete operation failed for lead: {lead_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "type": "DELETE_FAILED",
                    "message": "Failed to delete lead",
                    "details": {"lead_id": lead_id}
                }
            )

        logger.info(f"Successfully deleted lead '{business_name}' ({lead_id})")

        return DeleteLeadResponse(
            success=True,
            message=f"Lead '{business_name}' and associated outreach deleted successfully",
            error=None
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise

    except Exception as e:
        logger.error(f"Failed to delete lead {lead_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "type": "DATABASE_ERROR",
                "message": "Failed to delete lead from database",
                "details": {"error": str(e), "lead_id": lead_id}
            }
        )
