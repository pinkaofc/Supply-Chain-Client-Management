from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

@dataclass
class EmailState:
    """
    Represents the state of the email processing workflow.
    """
    emails: List[Dict[str, Any]] = field(default_factory=list)
    history: List[Dict[str, Any]] = field(default_factory=list) # Keeps track of past actions/states if needed
    metadata: Dict[str, Dict[str, Any]] = field(default_factory=dict) # General metadata for tracking, keyed by email_id

    current_email: Dict[str, Any] = field(default_factory=dict) # The email currently being processed
    current_email_id: Optional[str] = None # Added for convenience and clarity

    # Fields to store outputs from agents
    classification: Optional[str] = None   # Renamed from sentiment to classification for clarity
    summary: Optional[str] = None     # Summary from summarization_agent
    generated_response_body: Optional[str] = None # To explicitly store the final response text

    # For error tracking
    processing_error: Optional[str] = None # To store any error during processing of current_email

    # Flags for human review and sending status
    requires_human_review: bool = False
    # Removed: response_sent: bool = False (Handled by response_status_action string in main.py logging)
    # Removed: response_drafted: bool = False (Handled by response_status_action string in main.py logging)