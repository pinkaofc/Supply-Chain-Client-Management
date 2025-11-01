import json
import os
import time
from datetime import datetime
from pathlib import Path

# Config
from config import (
    EMAIL_USERNAME, EMAIL_APP_PASSWORD, IMAP_SERVER,
    YOUR_NAME, YOUR_GMAIL_ADDRESS_FOR_DRAFTS
)

# Utils
from utils.logger import get_logger
from utils.records_manager import log_email_record, initialize_csv, RECORDS_CSV_PATH, CSV_HEADERS
from core.email_sender import extract_name_from_email

# Core components
from core.email_ingestion import fetch_email
from core.supervisor import supervisor_langgraph
from core.email_sender import send_email, send_draft_to_gmail
from core.state import EmailState

logger = get_logger(__name__)

def handle_email_sending(final_state: EmailState, user_name: str, dry_run: bool) -> str:
    email_data = final_state.current_email
    generated_response = final_state.generated_response_body
    original_sender_email = email_data.get("sender_email", "unknown@example.com")
    original_subject = email_data.get("subject", "No Subject")

    if not generated_response or final_state.processing_error:
        logger.warning(f"Skipping send/draft for email ID {final_state.current_email_id} due to no response or error.")
        return "Skipped (No Response/Error)"

    email_for_sending = {
        "subject": original_subject,
        "response": generated_response,
        "from": original_sender_email
    }

    if dry_run or final_state.requires_human_review:
        logger.info(f"Email ID {final_state.current_email_id} flagged for human review or in dry-run mode. Sending draft to '{YOUR_GMAIL_ADDRESS_FOR_DRAFTS}'.")
        if send_draft_to_gmail(email_for_sending, user_name, YOUR_GMAIL_ADDRESS_FOR_DRAFTS):
            return "Drafted"
        else:
            logger.error(f"Failed to send draft for email ID {final_state.current_email_id}.")
            return "Draft Failed"
    else:
        logger.info(f"Email ID {final_state.current_email_id} is ready to be sent. Replying to '{original_sender_email}'.")
        if send_email(email_for_sending, user_name):
            return "Sent Directly"
        else:
            logger.error(f"Failed to send direct reply for email ID {final_state.current_email_id}.")
            return "Send Failed"

def main():
    logger.info("Starting email automation main script.")

    # Exit option before starting
    if input("Press Enter to continue or type 'exit' to stop: ").strip().lower() == "exit":
        print("Exiting script.")
        return

    initialize_csv(RECORDS_CSV_PATH)

    simulate_fetch = input("Use simulated emails from sample_emails.json? (y/n): ").strip().lower() == "y"
    email_limit = int(input("How many emails to process (max)? (e.g., 1): ") or "1")
    dry_run_send = input("Send all responses as DRAFTS to your Gmail address (dry run)? (y/n): ").strip().lower() == "y"
    mark_as_seen = input("Mark fetched emails as 'seen' on IMAP server (only for real fetch)? (y/n): ").strip().lower() == "y" if not simulate_fetch else False

    your_name = YOUR_NAME
    gmail_draft_address = YOUR_GMAIL_ADDRESS_FOR_DRAFTS
    logger.info(f"Your signature will be: {your_name}")
    logger.info(f"Drafts will be sent to: {gmail_draft_address}")

    logger.info("Fetching emails...")
    emails_to_process = fetch_email(
        simulate=simulate_fetch,
        limit=email_limit,
        mark_as_seen=mark_as_seen
    )

    if not emails_to_process:
        logger.info("No emails found to process. Exiting.")
        return

    logger.info(f"Fetched {len(emails_to_process)} emails.")
    sr_no_counter = 0

    for i, email_data_raw in enumerate(emails_to_process):
        sr_no_counter += 1
        email_id = email_data_raw.get("id", f"simulated_{i+1}")
        sender_email = email_data_raw.get("sender_email", "unknown@example.com")
        sender_name = email_data_raw.get("sender_name", extract_name_from_email(sender_email))
        subject = email_data_raw.get("subject", "No Subject")

        logger.info(f"\n--- Processing Email {sr_no_counter} (ID: {email_id}) ---")
        logger.info(f"Subject: {subject}")
        logger.info(f"From: {sender_name} <{sender_email}>")

        try:
            recipient_name_for_llm = extract_name_from_email(sender_email)

            final_state: EmailState = supervisor_langgraph(
                selected_email=email_data_raw,
                your_name=your_name,
                recipient_name=recipient_name_for_llm
            )

            logger.debug(f"Email ID {email_id} final state: Classification='{final_state.classification}', "
                         f"Summary length={len(final_state.summary or '')}, "
                         f"Response length={len(final_state.generated_response_body or '')}, "
                         f"Requires Review={final_state.requires_human_review}, "
                         f"Error='{final_state.processing_error}'")

            if final_state.processing_error:
                response_status_action = "Error During Processing"
                logger.error(f"Skipping send/draft for email ID {email_id} due to prior processing error: {final_state.processing_error}")
            elif final_state.classification in ["spam", "promotional"]:
                response_status_action = f"Skipped ({final_state.classification.capitalize()})"
                logger.info(f"Skipping send/draft for email ID {email_id} as it was classified as '{final_state.classification}'.")
            else:
                response_status_action = handle_email_sending(final_state, your_name, dry_run_send)

        except Exception as e:
            logger.critical(f"A critical error occurred while processing email ID {email_id}: {e}", exc_info=True)
            final_state = EmailState(
                current_email=email_data_raw,
                current_email_id=email_id,
                classification="error",
                summary="Processing failed due to critical error.",
                generated_response_body="Error occurred during processing.",
                processing_error=f"Critical error: {str(e)}"
            )
            response_status_action = "Critical Error"

        record_data_to_log = {
            'SR No': sr_no_counter,
            'Timestamp': email_data_raw.get('timestamp') or datetime.now().isoformat(),
            'Sender Email': sender_email,
            'Sender Name': sender_name,
            'Recipient Email': EMAIL_USERNAME,
            'Original Subject': subject,
            'Original Content': email_data_raw.get('body', ''),
            'Classification': final_state.classification,
            'Summary': final_state.summary,
            'Generated Response': final_state.generated_response_body,
            'Requires Human Review': final_state.requires_human_review,
            'Response Status': response_status_action,
            'Processing Error': final_state.processing_error,
            'Record Save Time': datetime.now().isoformat()
        }

        log_email_record(record_data_to_log, RECORDS_CSV_PATH)

        if i < len(emails_to_process) - 1:
            time.sleep(10)

    logger.info("All selected emails processed. Automation workflow finished.")

if __name__ == "__main__":
    main()