"""
Outreach Router - Manage outreach email generation and sending.

This router provides endpoints for regenerating outreach emails and
marking them as sent (email delivery integration pending).
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field

from services.supabase_service import SupabaseService
from services.auth_service import get_current_user
from services.email_service import send_email
from agents.outreach_agent import generate_outreach
from models.lead import Lead
from models.outreach import Outreach

logger = logging.getLogger(__name__)

# Initialize router with prefix and tags
router = APIRouter(
    prefix="/api/outreach",
    tags=["Outreach"]
)

# Initialize Supabase service
db = SupabaseService()


# Response Models

class OutreachResponse(BaseModel):
    """Response for outreach operations."""
    success: bool = Field(..., description="Whether the operation was successful")
    data: Optional[Outreach] = Field(None, description="Outreach record")
    error: Optional[Dict[str, Any]] = Field(None, description="Error details if failed")


class UpdateOutreachRequest(BaseModel):
    """Request body for updating outreach."""
    subject: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)


class SendResponse(BaseModel):
    """Response for send email operation."""
    success: bool = Field(..., description="Whether email was marked as sent")
    message: str = Field(..., description="Confirmation message")
    data: Optional[Outreach] = Field(None, description="Updated outreach record")
    error: Optional[Dict[str, Any]] = Field(None, description="Error details if failed")

@router.put(
    "/{outreach_id}",
    response_model=OutreachResponse,
    status_code=status.HTTP_200_OK,
    summary="Update outreach record",
    description="Manually update subject and message of an outreach record scoped to user"
)
async def update_outreach(
    outreach_id: str, 
    request: UpdateOutreachRequest,
    current_user_id: str = Depends(get_current_user)
) -> OutreachResponse:
    """
    Update outreach record scoped to user.
    """
    logger.info(f"Updating outreach: {outreach_id} for user {current_user_id}")

    try:
        updated_dict = await db.update_outreach(outreach_id, request.model_dump(), user_id=current_user_id)
        outreach = Outreach(**updated_dict)
        return OutreachResponse(success=True, data=outreach, error=None)
    except Exception as e:
        logger.error(f"Failed to update outreach {outreach_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to update outreach", "details": str(e)}
        )


@router.get(
    "/{lead_id}",
    response_model=OutreachResponse,
    status_code=status.HTTP_200_OK,
    summary="Get outreach by lead ID",
    description="Retrieve outreach record for a specific lead scoped to user"
)
async def get_outreach(
    lead_id: str,
    current_user_id: str = Depends(get_current_user)
) -> OutreachResponse:
    """
    Get outreach record for a lead scoped to user.
    """
    logger.info(f"Fetching outreach for lead: {lead_id} (User: {current_user_id})")

    try:
        outreach_dict = await db.get_outreach_by_lead(lead_id, user_id=current_user_id)

        if not outreach_dict:
            logger.warning(f"Outreach not found for lead: {lead_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "type": "OUTREACH_NOT_FOUND",
                    "message": f"Outreach for lead '{lead_id}' not found",
                    "details": {"lead_id": lead_id}
                }
            )

        outreach = Outreach(**outreach_dict)
        return OutreachResponse(success=True, data=outreach, error=None)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch outreach for lead {lead_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "type": "DATABASE_ERROR",
                "message": "Failed to retrieve outreach",
                "details": {"error": str(e)}
            }
        )

@router.post(
    "/{lead_id}/regenerate",
    response_model=OutreachResponse,
    status_code=status.HTTP_200_OK,
    summary="Regenerate outreach email",
    description="Generate a new personalized outreach email for an existing lead scoped to user"
)
async def regenerate_outreach(
    lead_id: str, 
    tone: Optional[str] = None,
    current_user_id: str = Depends(get_current_user)
) -> OutreachResponse:
    """
    Regenerate outreach email for an existing lead scoped to user.
    """
    logger.info(f"Regenerating outreach for lead: {lead_id} (User: {current_user_id})")

    try:
        # Fetch lead from database scoped to user
        lead_dict = await db.get_lead(lead_id, user_id=current_user_id)

        if not lead_dict:
            logger.warning(f"Lead not found or access denied: {lead_id}")
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

        # Prepare lead data for outreach agent
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

        # Prepare analysis data from lead
        analysis = {
            "opportunity_score": lead.opportunity_score,
            "identified_problem": lead.identified_problem,
            "website_benefits": lead.website_benefits,
            "estimated_value": lead.estimated_value
        }

        # Generate new outreach email
        new_outreach = await generate_outreach(lead_data, analysis, tone=tone)
        new_outreach.lead_id = lead_id

        # Check if outreach already exists scoped to user
        existing_outreach = await db.get_outreach_by_lead(lead_id, user_id=current_user_id)

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
                user_id=current_user_id
            )

            final_outreach = Outreach(**updated_dict)
        else:
            outreach_dict = new_outreach.model_dump()
            created_dict = await db.create_outreach(outreach_dict, user_id=current_user_id)
            final_outreach = Outreach(**created_dict)

        return OutreachResponse(
            success=True,
            data=final_outreach,
            error=None
        )

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
    description="Send an outreach email via Resend API scoped to user"
)
async def send_outreach(
    outreach_id: str,
    current_user_id: str = Depends(get_current_user)
) -> SendResponse:
    """
    Send outreach email and mark as sent, scoped to user.
    """
    logger.info(f"Sending outreach: {outreach_id} (User: {current_user_id})")

    try:
        # Fetch outreach record by ID scoped to user
        outreach_dict = await db.get_outreach_by_id(outreach_id, user_id=current_user_id)

        if not outreach_dict:
            logger.warning(f"Outreach not found or access denied: {outreach_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Outreach not found or access denied"}
            )

        # Check if already sent
        if outreach_dict.get("sent", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Outreach email has already been sent"}
            )

        # Fetch lead to get the recipient email scoped to user
        lead_id = str(outreach_dict.get("lead_id"))
        lead_dict = await db.get_lead(lead_id, user_id=current_user_id)
        if not lead_dict or not lead_dict.get("email"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Lead email not found"}
            )
        
        recipient_email = lead_dict["email"]

        # Send email via Resend
        await send_email(
            to_email=recipient_email,
            subject=outreach_dict["subject"],
            body=outreach_dict["message"]
        )

        # Mark as sent scoped to user
        updated_dict = await db.mark_outreach_sent(outreach_id, user_id=current_user_id)
        
        updated_outreach = Outreach(**updated_dict)

        return SendResponse(
            success=True,
            message="Outreach email sent successfully",
            data=updated_outreach,
            error=None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send outreach: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
