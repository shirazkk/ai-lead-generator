"""
Leads Router - CRUD operations for lead management.
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, status, Query, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

from services.supabase_service import SupabaseService
from services.auth_service import get_current_user
from models.lead import Lead
from models.outreach import Outreach

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/leads",
    tags=["Leads"]
)

db = SupabaseService()
security = HTTPBearer()


def get_access_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    return credentials.credentials


# ─── Response Models ───────────────────────────────────────────────────────────

class LeadWithOutreach(BaseModel):
    lead: Lead
    outreach: Optional[Outreach] = None


class LeadsListResponse(BaseModel):
    success: bool
    data: List[Lead]
    total: int
    error: Optional[Dict[str, Any]] = None


class LeadDetailResponse(BaseModel):
    success: bool
    data: Optional[LeadWithOutreach] = None
    error: Optional[Dict[str, Any]] = None


class DeleteLeadResponse(BaseModel):
    success: bool
    message: str
    error: Optional[Dict[str, Any]] = None


# ─── Endpoints ─────────────────────────────────────────────────────────────────

@router.get(
    "",
    response_model=LeadsListResponse,
    status_code=status.HTTP_200_OK,
    summary="List leads with filters",
)
async def list_leads(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    city: Optional[str] = Query(None),
    min_score: Optional[int] = Query(None, ge=1, le=10),
    max_score: Optional[int] = Query(None, ge=1, le=10),
    current_user_id: str = Depends(get_current_user),
    access_token: str = Depends(get_access_token),
) -> LeadsListResponse:
    logger.info(
        f"Fetching leads for user {current_user_id}: limit={limit}, offset={offset}, "
        f"city={city}, min_score={min_score}, max_score={max_score}"
    )
    try:
        filters = {}
        if city:
            filters["city"] = city
        if min_score is not None:
            filters["min_score"] = str(min_score)
        if max_score is not None:
            filters["max_score"] = str(max_score)

        lead_dicts = await db.get_leads(
            user_id=current_user_id,
            limit=limit,
            offset=offset,
            filters=filters if filters else None,
            access_token=access_token,
        )

        logger.info(f"Retrieved {len(lead_dicts)} raw records for user {current_user_id}")

        if len(lead_dicts) == 0:
            all_leads = await db.get_leads(
                user_id=current_user_id,
                limit=5,
                offset=0,
                access_token=access_token
            )
            logger.info(f"Total leads found for user {current_user_id} (unfiltered): {len(all_leads)}")

        leads = [Lead(**lead_dict) for lead_dict in lead_dicts]
        logger.info(f"Successfully retrieved {len(leads)} leads")

        return LeadsListResponse(success=True, data=leads, total=len(leads))

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
)
async def get_lead(
    lead_id: str,
    current_user_id: str = Depends(get_current_user),
    access_token: str = Depends(get_access_token),
) -> LeadDetailResponse:
    logger.info(f"Fetching lead: {lead_id} (User: {current_user_id})")
    try:
        lead_dict = await db.get_lead(
            lead_id,
            user_id=current_user_id,
            access_token=access_token
        )

        if not lead_dict:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "type": "LEAD_NOT_FOUND",
                    "message": f"Lead with ID '{lead_id}' not found",
                    "details": {"lead_id": lead_id}
                }
            )

        lead = Lead(**lead_dict)

        outreach_dict = await db.get_outreach_by_lead(
            lead_id,
            user_id=current_user_id,
            access_token=access_token
        )
        outreach = Outreach(**outreach_dict) if outreach_dict else None

        logger.info(f"Successfully retrieved lead '{lead.business_name}'")

        return LeadDetailResponse(
            success=True,
            data=LeadWithOutreach(lead=lead, outreach=outreach)
        )

    except HTTPException:
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
)
async def delete_lead(
    lead_id: str,
    current_user_id: str = Depends(get_current_user),
    access_token: str = Depends(get_access_token),
) -> DeleteLeadResponse:
    logger.info(f"Deleting lead: {lead_id} (User: {current_user_id})")
    try:
        lead_dict = await db.get_lead(
            lead_id,
            user_id=current_user_id,
            access_token=access_token
        )

        if not lead_dict:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "type": "LEAD_NOT_FOUND",
                    "message": f"Lead with ID '{lead_id}' not found",
                    "details": {"lead_id": lead_id}
                }
            )

        business_name = lead_dict.get("business_name", "Unknown")

        deleted = await db.delete_lead(
            lead_id,
            user_id=current_user_id,
            access_token=access_token
        )

        if not deleted:
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
            message=f"Lead '{business_name}' and associated outreach deleted successfully"
        )

    except HTTPException:
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