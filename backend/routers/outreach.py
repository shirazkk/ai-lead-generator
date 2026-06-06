"""
Outreach Router - Manage outreach email generation and sending.

This router provides endpoints for regenerating outreach emails and
marking them as sent (email delivery integration pending).
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from services.supabase_service import SupabaseService
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
    description="Manually update subject and message of an outreach record"
)
async def update_outreach(outreach_id: str, request: UpdateOutreachRequest) -> OutreachResponse:
    """
    Update outreach record.
    """
    logger.info(f"Updating outreach: {outreach_id}")

    try:
        updated_dict = await db.update_outreach(outreach_id, request.model_dump())
        outreach = Outreach(**updated_dict)
        return OutreachResponse(success=True, data=outreach, error=None)
    except Exception as e:
        logger.error(f"Failed to update outreach {outreach_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to update outreach", "details": str(e)}
        )


class SendResponse(BaseModel):
    """Response for send email operation."""
    success: bool = Field(..., description="Whether email was marked as sent")
    message: str = Field(..., description="Confirmation message")
    data: Optional[Outreach] = Field(None, description="Updated outreach record")
    error: Optional[Dict[str, Any]] = Field(None, description="Error details if failed")


@router.get(
    "/{lead_id}",
    response_model=OutreachResponse,
    status_code=status.HTTP_200_OK,
    summary="Get outreach by lead ID",
    description="Retrieve outreach record for a specific lead"
)
async def get_outreach(lead_id: str) -> OutreachResponse:
    """
    Get outreach record for a lead.
    """
    logger.info(f"Fetching outreach for lead: {lead_id}")

    try:
        outreach_dict = await db.get_outreach_by_lead(lead_id)

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
    description="Generate a new personalized outreach email for an existing lead"
)
async def regenerate_outreach(lead_id: str, tone: Optional[str] = None) -> OutreachResponse:
    """
    Regenerate outreach email for an existing lead.

    This endpoint fetches the lead data, runs the Outreach Agent to generate
    a new personalized email, and updates the existing outreach record (or
    creates a new one if none exists).

    Args:
        lead_id: UUID of the lead to regenerate outreach for

    Returns:
        OutreachResponse with newly generated outreach data

    Raises:
        HTTPException: If lead not found or generation fails
    """
    logger.info(f"Regenerating outreach for lead: {lead_id}")

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

        logger.info(f"Found lead: '{lead.business_name}'")

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
        logger.info(f"Generating new outreach for '{lead.business_name}' with tone: {tone}")
        new_outreach = await generate_outreach(lead_data, analysis) # NOTE: generate_outreach might need updating to accept tone if it's not currently used.

        # Ensure lead_id is set correctly
        new_outreach.lead_id = lead_id

        # Check if outreach already exists
        existing_outreach = await db.get_outreach_by_lead(lead_id)

        if existing_outreach:
            # Update existing outreach record
            logger.info(f"Updating existing outreach record: {existing_outreach['id']}")

            outreach_updates = {
                "subject": new_outreach.subject,
                "message": new_outreach.message,
                "tone": new_outreach.tone,
                "generated_at": new_outreach.generated_at.isoformat(),
                "sent": False,  # Reset sent status
                "sent_at": None
            }

            updated_dict = await db.update_outreach(
                existing_outreach["id"],
                outreach_updates
            )

            final_outreach = Outreach(**updated_dict)
            logger.info(f"Successfully updated outreach for '{lead.business_name}'")
        else:
            # Create new outreach record
            logger.info(f"Creating new outreach record for lead: {lead_id}")

            outreach_dict = new_outreach.model_dump()
            created_dict = await db.create_outreach(outreach_dict)

            final_outreach = Outreach(**created_dict)
            logger.info(f"Successfully created outreach for '{lead.business_name}'")

        return OutreachResponse(
            success=True,
            data=final_outreach,
            error=None
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise

    except Exception as e:
        logger.error(f"Failed to regenerate outreach for lead {lead_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "type": "GENERATION_FAILED",
                "message": "Failed to regenerate outreach email",
                "details": {"error": str(e), "lead_id": lead_id}
            }
        )


@router.post(
    "/send/{outreach_id}",
    response_model=SendResponse,
    status_code=status.HTTP_200_OK,
    summary="Send outreach email",
    description="Send an outreach email via Resend API and mark it as sent"
)
async def send_outreach(outreach_id: str) -> SendResponse:
    """
    Send outreach email and mark as sent.

    This endpoint fetches outreach and lead data, sends the email
    using the Resend API, and updates the database upon success.
    """
    logger.info(f"Sending outreach: {outreach_id}")

    try:
        # Fetch outreach record by ID
        outreach_dict = await db.get_outreach_by_id(outreach_id)

        if not outreach_dict:
            logger.warning(f"Outreach not found: {outreach_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "type": "OUTREACH_NOT_FOUND",
                    "message": f"Outreach with ID '{outreach_id}' not found",
                    "details": {"outreach_id": outreach_id}
                }
            )

        # Check if already sent
        if outreach_dict.get("sent", False):
            sent_at = outreach_dict.get("sent_at")
            logger.warning(f"Outreach already sent: {outreach_id} at {sent_at}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "type": "ALREADY_SENT",
                    "message": "Outreach email has already been sent",
                    "details": {
                        "outreach_id": outreach_id,
                        "sent_at": sent_at
                    }
                }
            )

        # Fetch lead to get the recipient email
        lead_id = outreach_dict.get("lead_id")
        lead_dict = await db.get_lead(lead_id)
        if not lead_dict or not lead_dict.get("email"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "type": "MISSING_RECIPIENT",
                    "message": "Lead email not found, cannot send outreach"
                }
            )
        
        recipient_email = lead_dict["email"]

        # Send email via Resend
        logger.info(f"Sending email to {recipient_email} for outreach {outreach_id}")
        await send_email(
            to_email=recipient_email,
            subject=outreach_dict["subject"],
            body=outreach_dict["message"]
        )

        # Mark as sent with timestamp
        updated_dict = await db.mark_outreach_sent(outreach_id)
        updated_outreach = Outreach(**updated_dict)

        logger.info(f"Successfully sent and marked outreach as sent: {outreach_id}")

        return SendResponse(
            success=True,
            message="Outreach email sent successfully",
            data=updated_outreach,
            error=None
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise

    except Exception as e:
        logger.error(f"Failed to send outreach {outreach_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "type": "SEND_FAILED",
                "message": "Failed to send outreach email",
                "details": {"error": str(e), "outreach_id": outreach_id}
            }
        )
