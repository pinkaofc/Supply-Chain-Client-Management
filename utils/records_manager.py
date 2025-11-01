# utils/record_manager.py
import csv
from pathlib import Path
from typing import Dict, Any
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)

# Define the directory where records will be saved
RECORDS_DIR = Path(__file__).parent.parent / "records"
RECORDS_CSV_PATH = RECORDS_DIR / "records.csv"

# Define CSV headers - make sure these match the keys you'll use in log_email_record
CSV_HEADERS = [
    'SR No', 'Timestamp', 'Sender Email', 'Sender Name', 'Recipient Email',
    'Original Subject', 'Original Content', 'Classification', 'Summary',
    'Generated Response', 'Requires Human Review', 'Response Status',
    'Processing Error', 'Record Save Time'
]

def initialize_csv(csv_path: Path = RECORDS_CSV_PATH):
    """
    Ensures the CSV file exists with headers in the specified records directory.
    """
    csv_path.parent.mkdir(parents=True, exist_ok=True) # Create 'records' directory if it doesn't exist
    
    if not csv_path.exists():
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADERS)
        logger.info(f"Initialized {csv_path} with headers.")
    else:
        logger.debug(f"{csv_path} already exists.")

def log_email_record(record_data: Dict[str, Any], csv_path: Path = RECORDS_CSV_PATH):
    """
    Appends a single email processing record to the CSV file.
    The record_data dict should have keys matching CSV_HEADERS.
    """
    initialize_csv(csv_path) # Ensure headers are present

    # Prepare data for DictWriter, filling missing fields or ensuring order
    row_to_write = {header: record_data.get(header, '') for header in CSV_HEADERS}

    with open(csv_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        writer.writerow(row_to_write)
    logger.info(f"Logged record for email ID {record_data.get('SR No', 'N/A')} from {record_data.get('Sender Email', 'N/A')}")