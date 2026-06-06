"""
Outreach model - Email outreach data.

This model represents generated outreach emails ready to be sent to leads,
with tracking information for delivery status.
"""

from typing import Optional
from datetime import datetime, timezone
from uuid import uuid4
from pydantic import BaseModel, Field, field_validator


class Outreach(BaseModel):
    """
    Outreach email model for lead communication.

    This is the output from the Email Writer Agent containing personalized
    outreach emails generated for qualified leads. Includes tracking fields
    for delivery status and timestamps.

    Attributes:
        id: Unique identifier for the outreach record
        lead_id: Reference to the associated lead
        subject: Email subject line
        message: Email body content
        tone: Communication tone (friendly/professional/casual)
        generated_at: Timestamp when email was generated
        sent: Whether the email has been sent
        sent_at: Timestamp when email was sent (if applicable)
    """

    id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique identifier for the outreach record"
    )
    lead_id: str = Field(
        ...,
        description="Reference to the associated lead ID",
        min_length=1
    )
    subject: str = Field(
        ...,
        description="Email subject line",
        min_length=1,
        max_length=200
    )
    message: str = Field(
        ...,
        description="Email body content with personalized messaging",
        min_length=1
    )
    tone: str = Field(
        ...,
        description="Communication tone: 'friendly' | 'professional' | 'casual'"
    )
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the email was generated"
    )
    sent: bool = Field(
        False,
        description="Whether the email has been sent"
    )
    sent_at: Optional[datetime] = Field(
        None,
        description="Timestamp when the email was sent (only set when sent=True)"
    )

    @field_validator("tone")
    @classmethod
    def validate_tone(cls, v: str) -> str:
        """
        Validate tone is one of the allowed values.

        Args:
            v: The tone value

        Returns:
            The validated tone

        Raises:
            ValueError: If tone is not 'friendly', 'professional', or 'casual'
        """
        allowed_tones = {"friendly", "professional", "casual"}
        if v not in allowed_tones:
            raise ValueError(
                f"tone must be one of {allowed_tones}, got '{v}'"
            )
        return v

    @field_validator("sent_at")
    @classmethod
    def validate_sent_at(cls, v: Optional[datetime], info) -> Optional[datetime]:
        """
        Validate sent_at is only set when sent is True.

        Args:
            v: The sent_at value
            info: Validation context containing other field values

        Returns:
            The validated sent_at timestamp

        Raises:
            ValueError: If sent_at is set but sent is False
        """
        # Get the value of 'sent' from the validation context
        sent = info.data.get("sent", False)

        if v is not None and not sent:
            raise ValueError("sent_at can only be set when sent is True")

        return v

    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
                "id": "660e8400-e29b-41d4-a716-446655440000",
                "lead_id": "550e8400-e29b-41d4-a716-446655440000",
                "subject": "Grow Joe's Pizza with a Professional Website",
                "message": "Hi Joe,\n\nI came across Joe's Pizza on Google Maps and was impressed by your 4.5-star rating...",
                "tone": "friendly",
                "generated_at": "2026-06-06T06:53:22.692Z",
                "sent": False,
                "sent_at": None
            }
        }
