import smtplib
from email.message import EmailMessage
from config import EMAIL_SERVER, EMAIL_PASSWORD, EMAIL_USERNAME, EMAIL_PORT
from utils.logger import get_logger
from utils.formatter import clean_text, format_email
import email.utils # For robust name extraction

logger = get_logger(__name__)

def extract_name_from_email(email_address: str) -> str:
    """
    Extracts the display name or the local part of the email address.
    """
    name, addr = email.utils.parseaddr(email_address)
    if name:
        return name
    if "@" in email_address:
        return email_address.split("@")[0].capitalize() # Capitalize for a nicer name
    return "Customer" # Default fallback

def send_draft_to_gmail(email_data: dict, user_name: str, gmail_address: str) -> bool:
    """
    Sends a draft email to a specified Gmail address using SMTP.

    Arguments:
        email_data (dict): Email data with keys "subject", "response", "from".
        user_name (str): Your name to be used in the response.
        gmail_address (str): Destination Gmail address for the draft.

    Returns:
        bool: True if sent successfully, False otherwise.
    """
    try:
        subject = clean_text(email_data.get("subject", ""))
        raw_response_content = email_data.get("response", "").strip()
        original_sender_email = email_data.get("from", "") # This is the original sender's email
        
        # This sender_name is the original sender's name from the email we're drafting a reply to
        original_sender_name = extract_name_from_email(original_sender_email) 

        response_content = format_email(subject, original_sender_name, raw_response_content, user_name)

        msg = EmailMessage()
        msg["Subject"] = f"Draft: Re: {subject}"
        msg["From"] = EMAIL_USERNAME
        msg["To"] = gmail_address # The Gmail account to send the draft to
        msg.set_content(response_content)

        logger.debug("Connecting to SMTP server %s:%s for sending draft", EMAIL_SERVER, EMAIL_PORT)
        with smtplib.SMTP(EMAIL_SERVER, int(EMAIL_PORT)) as server:
            server.starttls()
            server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
            server.send_message(msg)
            logger.info("Draft sent to Gmail account at %s for review.", gmail_address)

        return True
    except Exception as e:
        logger.error("Failed to send draft to Gmail: %s", e, exc_info=True)
        return False

def send_email(email_data: dict, user_name: str) -> bool:
    """
    Sends an email reply via SMTP using the generated response.

    Arguments:
        email_data (dict): Email data with keys "subject", "response", "from".
        user_name (str): Your name to be used in the response.

    Returns:
        bool: True if sent successfully, False otherwise.
    """
    try:
        subject = clean_text(email_data.get("subject", ""))
        raw_response_content = email_data.get("response", "").strip()
        recipient_email = email_data.get("from", "") # Original sender is now the recipient
        
        # This sender_name is the original sender's name from the email we're replying to
        original_sender_name = extract_name_from_email(recipient_email) 

        response_content = format_email(subject, original_sender_name, raw_response_content, user_name)

        msg = EmailMessage()
        msg["Subject"] = f"Re: {subject}"
        msg["From"] = EMAIL_USERNAME
        msg["To"] = recipient_email
        msg.set_content(response_content)

        logger.debug("Connecting to SMTP server %s:%s", EMAIL_SERVER, EMAIL_PORT)
        with smtplib.SMTP(EMAIL_SERVER, int(EMAIL_PORT)) as server:
            server.starttls()
            server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
            server.send_message(msg)
            logger.info("Email sent to %s", recipient_email)

        return True
    except Exception as e:
        logger.error("Failed to send email to %s: %s", recipient_email, e, exc_info=True)
        return False