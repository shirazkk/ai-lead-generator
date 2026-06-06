import logging
import resend
from config import settings

# Configure Resend API Key
resend.api_key = settings.resend_api_key

logger = logging.getLogger(__name__)

async def send_email(to_email: str, subject: str, body: str) -> str:
    """
    Sends an email using the Resend API.

    Args:
        to_email: The recipient's email address
        subject: The email subject
        body: The email body content (HTML or plain text)

    Returns:
        The email ID from Resend if successful

    Raises:
        Exception: If email sending fails
    """
    try:
        logger.info(f"Attempting to send email to {to_email}")
        
        params = {
            "from": "onboarding@resend.dev",  # Using default for now, should be configured in settings later
            "to": to_email,
            "subject": subject,
            "text": body,  # Using text for now.
        }

        response = resend.Emails.send(params)
        
        logger.info(f"Successfully sent email. ID: {response['id']}")
        return response['id']
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        raise Exception(f"Email delivery failed: {str(e)}")
