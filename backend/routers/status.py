"""
Status Router - Real-time progress tracking for lead generation jobs.

This router provides Server-Sent Events (SSE) streaming for monitoring
agent pipeline progress in real-time.
"""

import logging
import asyncio
import json
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from services.job_store import get_job_status
from services.auth_service import get_current_user

logger = logging.getLogger(__name__)

# Initialize router with prefix and tags
router = APIRouter(
    prefix="/api/status",
    tags=["Status"]
)

@router.get(
    "/{job_id}",
    summary="Get job status",
    description="Retrieve the current status for a lead generation job scoped to user"
)
async def get_job_status_endpoint(
    job_id: str,
    current_user_id: str = Depends(get_current_user)
):
    """
    Get job status scoped to user.
    """
    status_data = get_job_status(job_id, user_id=current_user_id)
    if not status_data:
        raise HTTPException(status_code=404, detail="Job not found or access denied")
    return {"success": True, "data": status_data}

@router.get(
    "/{job_id}/stream",
    summary="Stream job status",
    description="Stream real-time job progress via SSE, scoped to user."
)
async def stream_job_status(
    job_id: str,
    current_user_id: str = Depends(get_current_user)
):
    """
    Stream real-time job progress via SSE, scoped to user.
    """
    async def event_generator():
        while True:
            job_status = get_job_status(job_id, user_id=current_user_id)

            if not job_status:
                yield {"event": "error", "data": json.dumps({"message": "Job not found or access denied"})}
                break

            # Send progress update
            yield {
                "event": "progress",
                "data": json.dumps(job_status)
            }

            # Exit if job complete or failed
            if job_status.get("status") in ["completed", "failed"]:
                break

            await asyncio.sleep(1)  # Poll interval

    return EventSourceResponse(event_generator())
