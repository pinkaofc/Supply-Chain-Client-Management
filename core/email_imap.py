import imaplib
import email
from email.header import decode_header
from email.utils import parseaddr, parsedate_to_datetime
from bs4 import BeautifulSoup
from utils.logger import get_logger

logger = get_logger(__name__, log_to_file=True)
logger.info("Logger initialized successfully.")

def fetch_imap_emails(email_address, app_password, imap_server, imap_port=993, max_emails=1, mark_as_seen=False):
    """
    Fetches recent unread emails from the IMAP inbox and returns structured data.

    Arguments:
        email_address (str): Email address used for login.
        app_password (str): Gmail App Password.
        imap_server (str): IMAP server address.
        imap_port (int): IMAP port (default 993).
        max_emails (int): Number of recent emails to fetch.
        mark_as_seen (bool): If True, mark fetched emails as 'seen'.

    Returns:
        List[dict]: A list of normalized email dictionaries.
    """
    mail = None
    try:
        mail = imaplib.IMAP4_SSL(imap_server, imap_port)
        mail.login(email_address, app_password)
        mail.select("inbox")

        status, messages = mail.search(None, "UNSEEN")
        if status != 'OK':
            logger.error(f"Failed to search for unread emails: {messages}")
            return []

        email_ids = messages[0].split()
        if not email_ids:
            logger.info("No unread emails found.")
            return []

        email_ids = email_ids[-max_emails:]

        emails = []
        for num in email_ids:
            try:
                status, msg_data = mail.fetch(num, "(RFC822)")
                if status != 'OK':
                    logger.warning(f"Failed to fetch email ID {num.decode()}: {msg_data}")
                    continue

                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)

                # Decode subject
                subject_decoded = "(no subject)"
                try:
                    decoded_headers = decode_header(msg.get("Subject", "(no subject)"))
                    subject_parts = []
                    for s, encoding in decoded_headers:
                        if isinstance(s, bytes):
                            subject_parts.append(s.decode(encoding if encoding else "utf-8", errors="replace"))
                        else:
                            subject_parts.append(s)
                    subject_decoded = "".join(subject_parts)
                except Exception as e:
                    logger.warning(f"Could not decode subject for email ID {num.decode()}: {e}")

                # Parse sender name and email
                sender_name, sender_email = "Unknown", "unknown@example.com"
                sender_raw = msg.get("From", "Unknown <unknown@example.com>")
                try:
                    sender_name, sender_email = parseaddr(sender_raw)
                    if not sender_email:
                        sender_email = "unknown@example.com"
                except Exception as e:
                    logger.warning(f"Could not parse sender for email ID {num.decode()}: {e}")

                # Extract timestamp
                timestamp = None
                date_raw = msg.get("Date")
                if date_raw:
                    try:
                        timestamp = parsedate_to_datetime(date_raw).isoformat()
                    except Exception as e:
                        logger.warning(f"Could not parse date for email ID {num.decode()}: {e}")

                body = extract_email_body(msg)

                emails.append({
                    "id": num.decode(),
                    "subject": subject_decoded,
                    "body": body,
                    "sender_name": sender_name,
                    "sender_email": sender_email,
                    "timestamp": timestamp
                })

                if mark_as_seen:
                    mail.store(num, '+FLAGS', '\\Seen')
                    logger.debug(f"Marked email ID {num.decode()} as seen.")

            except Exception as e:
                logger.error(f"Error processing email ID {num.decode()}: {e}", exc_info=True)
                continue

    except imaplib.IMAP4.error as e:
        logger.error(f"IMAP login or server error: {e}")
        return []
    except Exception as e:
        logger.error(f"An unexpected error occurred in fetch_imap_emails: {e}", exc_info=True)
        return []
    finally:
        if mail:
            try:
                mail.logout()
            except imaplib.IMAP4.error as e:
                logger.warning(f"Error during IMAP logout: {e}")
            except Exception as e:
                logger.warning(f"Unexpected error during IMAP logout: {e}")

    return emails

def extract_email_body(msg):
    """
    Extracts the plain text body from an email message.
    Prioritizes text/plain, falls back to text/html (converting to plain text).
    """
    body_content = []

    for part in msg.walk():
        content_type = part.get_content_type()
        content_disposition = str(part.get("Content-Disposition"))

        if content_type == "text/plain" and "attachment" not in content_disposition:
            charset = part.get_content_charset() or "utf-8"
            try:
                payload = part.get_payload(decode=True).decode(charset, errors="replace")
                if payload.strip():
                    body_content.append(payload)
            except Exception as e:
                logger.warning(f"Failed to decode plain text part: {e}")

    if body_content:
        return "\n".join(body_content).strip()

    for part in msg.walk():
        content_type = part.get_content_type()
        content_disposition = str(part.get("Content-Disposition"))
        if content_type == "text/html" and "attachment" not in content_disposition:
            charset = part.get_content_charset() or "utf-8"
            try:
                html_payload = part.get_payload(decode=True).decode(charset, errors="replace")
                soup = BeautifulSoup(html_payload, "html.parser")
                for script_or_style in soup(["script", "style"]):
                    script_or_style.decompose()
                text = soup.get_text()
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for phrase in lines if phrase.strip())
                text_body = '\n'.join(chunks)
                if text_body:
                    return text_body
            except ImportError:
                logger.warning("BeautifulSoup not installed. Cannot convert HTML to plain text.")
                return "HTML content present but not processed (BeautifulSoup missing)."
            except Exception as e:
                logger.warning(f"Failed to decode or convert HTML part: {e}")

    return ""