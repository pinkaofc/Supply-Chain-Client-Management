# config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Gemini API Key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# SMTP Email Configuration (for sending replies)
EMAIL_SERVER = os.getenv("EMAIL_SERVER", "smtp.gmail.com") # Added default
EMAIL_USERNAME = os.getenv("EMAIL_USERNAME")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD") # This might be an App Password for SMTP as well
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))  # Default to 587 if not set

# IMAP Configuration (for fetching emails)
IMAP_USERNAME = os.getenv("IMAP_USERNAME", EMAIL_USERNAME) # Default to EMAIL_USERNAME
IMAP_PASSWORD = os.getenv("IMAP_PASSWORD", EMAIL_PASSWORD) # Default to EMAIL_PASSWORD, but will be overridden by EMAIL_APP_PASSWORD if set
IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.gmail.com")
IMAP_PORT = int(os.getenv("IMAP_PORT", 993))  # Default to 993 for SSL

# Gmail App Password (This is often specifically used for IMAP and SMTP when 2FA is on)
# Make sure this variable is used consistently for IMAP/SMTP authentication in core/email_sender and core/email_imap
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")

# Your personal details for the agent (ADD THESE LINES)
YOUR_NAME = os.getenv("YOUR_NAME", "AI Agent") # Provide a default if not set
YOUR_GMAIL_ADDRESS_FOR_DRAFTS = os.getenv("YOUR_GMAIL_ADDRESS_FOR_DRAFTS", EMAIL_USERNAME)

# # Path for CSV records
# RECORDS_CSV_PATH = "emails_records.csv"