"""
Outreach Router - Manage outreach email generation and sending.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

from services.supabase_service import SupabaseService
from services.auth_service import get_current_user
from services.email_service import send_email
from agents.outreach_agent import generate_outreach
from models.lead import Lead
from models.outreach import Outreach

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/outreach",
    tags=["Outreach"]
)

db = SupabaseService()
security = HTTPBearer()


def get_access_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    return credentials.credentials


# ─── Response Models ───────────────────────────────────────────────────────────

class OutreachResponse(BaseModel):
    success: bool
    data: Optional[Outreach] = None
    error: Optional[Dict[str, Any]] = None


class UpdateOutreachRequest(BaseModel):
    subject: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)


class SendResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Outreach] = None
    error: Optional[Dict[str, Any]] = None


# ─── Endpoints ─────────────────────────────────────────────────────────────────

@router.get(
    "/{lead_id}",
    response_model=OutreachResponse,
    status_code=status.HTTP_200_OK,
    summary="Get outreach by lead ID",
)
async def get_outreach(
    lead_id: str,
    current_user_id: str = Depends(get_current_user),
    access_token: str = Depends(get_access_token),
) -> OutreachResponse:
    logger.info(f"Fetching outreach for lead: {lead_id} (User: {current_user_id})")
    try:
        outreach_dict = await db.get_outreach_by_lead(
            lead_id,
            user_id=current_user_id,
            access_token=access_token
        )

        if not outreach_dict:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "type": "OUTREACH_NOT_FOUND",
                    "message": f"Outreach for lead '{lead_id}' not found",
                    "details": {"lead_id": lead_id}
                }
            )

        return OutreachResponse(success=True, data=Outreach(**outreach_dict))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch outreach for lead {lead_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"type": "DATABASE_ERROR", "message": "Failed to retrieve outreach", "details": str(e)}
        )


@router.put(
    "/{outreach_id}",
    response_model=OutreachResponse,
    status_code=status.HTTP_200_OK,
    summary="Update outreach record",
)
async def update_outreach(
    outreach_id: str,
    request: UpdateOutreachRequest,
    current_user_id: str = Depends(get_current_user),
    access_token: str = Depends(get_access_token),
) -> OutreachResponse:
    logger.info(f"Updating outreach: {outreach_id} for user {current_user_id}")
    try:
        updated_dict = await db.update_outreach(
            outreach_id,
            request.model_dump(),
            user_id=current_user_id,
            access_token=access_token
        )
        return OutreachResponse(success=True, data=Outreach(**updated_dict))
    except Exception as e:
        logger.error(f"Failed to update outreach {outreach_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to update outreach", "details": str(e)}
        )


@router.post(
    "/{lead_id}/regenerate",
    response_model=OutreachResponse,
    status_code=status.HTTP_200_OK,
    summary="Regenerate outreach email",
)
async def regenerate_outreach(
    lead_id: str,
    tone: Optional[str] = None,
    current_user_id: str = Depends(get_current_user),
    access_token: str = Depends(get_access_token),
) -> OutreachResponse:
    logger.info(f"Regenerating outreach for lead: {lead_id} (User: {current_user_id})")
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

        lead_data = {
            "id": lead.id,
            "business_name": lead.business_name,
            "owner_name": lead.owner_name,
            "city": lead.city,
            "address": lead.address,
            "phone": lead.phone,
            "email": lead.email,
            "description": lead.business_description
        }

        analysis = {
            "opportunity_score": lead.opportunity_score,
            "identified_problem": lead.identified_problem,
            "website_benefits": lead.website_benefits,
            "estimated_value": lead.estimated_value
        }

        new_outreach = await generate_outreach(lead_data, analysis, tone=tone)
        new_outreach.lead_id = lead_id

        existing_outreach = await db.get_outreach_by_lead(
            lead_id,
            user_id=current_user_id,
            access_token=access_token
        )

        if existing_outreach:
            outreach_updates = {
                "subject": new_outreach.subject,
                "message": new_outreach.message,
                "tone": new_outreach.tone,
                "generated_at": new_outreach.generated_at.isoformat(),
                "sent": False,
                "sent_at": None
            }
            updated_dict = await db.update_outreach(
                existing_outreach["id"],
                outreach_updates,
                user_id=current_user_id,
                access_token=access_token
            )
            final_outreach = Outreach(**updated_dict)
        else:
            created_dict = await db.create_outreach(
                new_outreach.model_dump(),
                user_id=current_user_id,
                access_token=access_token
            )
            final_outreach = Outreach(**created_dict)

        return OutreachResponse(success=True, data=final_outreach)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to regenerate outreach: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to regenerate outreach email", "details": str(e)}
        )


@router.post(
    "/send/{outreach_id}",
    response_model=SendResponse,
    status_code=status.HTTP_200_OK,
    summary="Send outreach email",
)
async def send_outreach(
    outreach_id: str,
    current_user_id: str = Depends(get_current_user),
    access_token: str = Depends(get_access_token),
) -> SendResponse:
    logger.info(f"Sending outreach: {outreach_id} (User: {current_user_id})")
    try:
        outreach_dict = await db.get_outreach_by_id(
            outreach_id,
            user_id=current_user_id,
            access_token=access_token
        )

        if not outreach_dict:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Outreach not found or access denied"}
            )

        if outreach_dict.get("sent", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Outreach email has already been sent"}
            )

        lead_id = str(outreach_dict.get("lead_id"))
        lead_dict = await db.get_lead(
            lead_id,
            user_id=current_user_id,
            access_token=access_token
        )

        if not lead_dict or not lead_dict.get("email"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Lead email not found"}
            )

        await send_email(
            to_email=lead_dict["email"],
            subject=outreach_dict["subject"],
            body=outreach_dict["message"]
        )

        updated_dict = await db.mark_outreach_sent(
            outreach_id,
            user_id=current_user_id,
            access_token=access_token
        )

        return SendResponse(
            success=True,
            message="Outreach email sent successfully",
            data=Outreach(**updated_dict)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send outreach: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))