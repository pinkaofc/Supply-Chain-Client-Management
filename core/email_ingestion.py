import json
import socket
from pathlib import Path

# Correctly import IMAP_SERVER and IMAP_PORT from config
from config import EMAIL_USERNAME, EMAIL_APP_PASSWORD, IMAP_SERVER, IMAP_PORT # IMAP_PORT is crucial here

from utils.logger import get_logger
logger = get_logger(__name__, log_to_file=True)
logger.info("Logger initialized successfully.")

# Correct the import statement to match your filename
try:
    # Assuming core/email_imap.py exists and contains fetch_imap_emails
    from core.email_imap import fetch_imap_emails
    # Also, if email_imap.py uses BeautifulSoup, the import should be within that file
    # and beautifulsoup4 must be pip installed.
except ImportError as e:
    # Use a logger from utils.logger if available, or print directly
    # Assuming you have utils.logger configured, it's better to use it
    from utils.logger import get_logger
    logger = get_logger(__name__)
    logger.error(f"ERROR: Could not import fetch_imap_emails from core.email_imap: {e}. IMAP fetching will be unavailable. "
                 f"Ensure core/email_imap.py exists and `beautifulsoup4` is installed if HTML parsing is involved.")
    fetch_imap_emails = None
except ModuleNotFoundError as e:
    from utils.logger import get_logger
    logger = get_logger(__name__)
    logger.error(f"ERROR: A module required by fetch_imap_emails is missing: {e}. IMAP fetching will be unavailable. "
                 f"Ensure all dependencies (e.g., `beautifulsoup4`) are installed.")
    fetch_imap_emails = None


def is_running_locally(port: int = 8000) -> bool:
    """
    Checks if a given port is available on localhost, often used to infer
    if a local service is running or to find a free port.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1) # Add a timeout to prevent hanging
            s.bind(("localhost", port))
            return True # Port is free
    except OSError:
        return False # Port is in use or inaccessible
    except Exception as e:
        print(f"Error checking local port {port}: {e}") # Consider using logger here too
        return False

def fetch_email(simulate: bool = True, limit: int = 10, mark_as_seen: bool = False):
    """
    Fetches emails. If simulate=True, load emails from a JSON file.
    Otherwise, fetch from IMAP using Gmail app password.

    Arguments:
        simulate (bool): Whether to simulate email ingestion from a local file.
        limit (int): Number of emails to fetch if using IMAP.
        mark_as_seen (bool): If True, mark fetched emails as 'seen' on the IMAP server.

    Returns:
        List[dict]: A list of email dictionaries.
    """
    if simulate:
        email_file = Path(__file__).parent.parent / "sample_emails.json"
        try:
            with open(email_file, "r", encoding="utf-8") as f:
                emails = json.load(f)
            # Use logger instead of print
            logger.info(f"Loaded {len(emails)} simulated emails from {email_file}")
            return emails
        except FileNotFoundError:
            logger.error(f"Error: {email_file} not found. Ensure the JSON file is correctly placed.")
            return []
        except json.JSONDecodeError:
            logger.error(f"Error: Could not decode {email_file}. Check its format.")
            return []
    else:
        if not fetch_imap_emails:
            raise ImportError("IMAP fetching is not available. Please ensure core/email_imap.py is correct and dependencies are met.")
        logger.info(f"Attempting to fetch {limit} unread emails from {IMAP_SERVER}:{IMAP_PORT} for {EMAIL_USERNAME}...")
        return fetch_imap_emails(
            email_address=EMAIL_USERNAME,
            app_password=EMAIL_APP_PASSWORD,
            imap_server=IMAP_SERVER,
            imap_port=IMAP_PORT,
            max_emails=limit,
            mark_as_seen=mark_as_seen
        )
