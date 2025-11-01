import json
from core.email_sender import send_email # Assuming this sends the final email
from config import EMAIL_USERNAME # Assuming this is your outgoing email address (e.g., support@shipcube.com)
from agents.response_agent import generate_response # Import the generation function
from agents.human_review_agent import review_email # Import the review function
from utils.logger import get_logger

logger = get_logger(__name__)

# --- Dummy function for summary for testing purposes ---
# In a real scenario, this would come from your summarization agent
def dummy_summarize_email(email_body: str) -> str:
    if "damaged goods" in email_body.lower():
        return "Customer reported damaged goods in order, requesting replacement/refund."
    elif "missing items" in email_body.lower():
        return "Customer reported missing items in shipment, requesting investigation/resend."
    elif "wrong address" in email_body.lower() or "incorrectly" in email_body.lower():
        return "Customer reported shipment delivered to wrong address, requesting investigation."
    elif "not received" in email_body.lower():
        return "Customer reported shipment marked delivered but not received."
    elif "appreciation" in email_body.lower() or "excellent service" in email_body.lower():
        return "Customer sent an appreciation email for a resolved issue."
    elif "delivery estimate" in email_body.lower() or "update" in email_body.lower():
        return "Customer requested delivery estimate/update for a PO."
    elif "invoice" in email_body.lower():
        return "Customer requested an invoice for a specific order."
    elif "warranty" in email_body.lower():
        return "Customer has an issue with a product warranty and needs guidance."
    elif "bulk order" in email_body.lower():
        return "Customer inquired about discounts for a bulk order."
    elif "feedback" in email_body.lower() and "exceptional" in email_body.lower():
        return "Customer provided positive feedback on delivery speed."
    elif "customs documentation" in email_body.lower():
        return "Customer requires additional customs documentation."
    elif "integration api" in email_body.lower() or "technical support" in email_body.lower():
        return "Customer needs technical support for API integration."
    else:
        return "Customer inquiry about a general topic."
# --------------------------------------------------------

def run_test_email_response_flow(email_data):
    # Your company's name, used in the signature
    # Assuming EMAIL_USERNAME is like "support@shipcube.com"
    your_company_name = "shipcube" # Or extract from EMAIL_USERNAME if it's like "Shipcube Support <support@shipcube.com>"

    # Extract recipient name for the greeting.
    # This is where you might need more sophisticated logic if "james.liu@..."
    # should result in a greeting of "Pinka".
    # For now, it will derive from the sender's email.
    recipient_email = email_data.get("from", "")
    # Simple extraction: "james.liu@fasttrackglobal.cn" -> "James"
    # If you need "Pinka" for "james.liu@..." you need a mapping or a more intelligent agent.
    if '@' in recipient_email:
        # Get part before @, then split by '.' and capitalize first part
        local_part = recipient_email.split('@')[0]
        # Attempt to get a friendly name, e.g., "james.liu" -> "James"
        # If 'itsprianka1230', it will be 'Itsprianka1230' - might need refinement.
        recipient_name_for_greeting = local_part.split('.')[0].capitalize()
    else:
        recipient_name_for_greeting = "Customer" # Fallback


    print(f"\n--- Processing Email ID: {email_data.get('id', 'N/A')} ---")
    print(f"From: {email_data.get('from')}")
    print(f"Subject: {email_data.get('subject')}")
    print(f"Body: {email_data.get('body')}")
    print("-------------------------------------")

    # 1. Summarize the email (using dummy for now)
    summary = dummy_summarize_email(email_data.get('body', ''))
    logger.info(f"Summary for email ID {email_data.get('id', 'N/A')}: {summary}")

    # 2. Generate the initial response
    # Pass recipient_name_for_greeting for the "Hi {name}," part
    # Pass your_company_name for the "Best regards, {name}" part
    generated_response = generate_response(
        email=email_data,
        summary=summary,
        recipient_name=recipient_name_for_greeting, # Used for the "Hi {name},"
        your_name=your_company_name # Used for the "Best regards, {name}"
    )
    
    logger.info(f"Initial AI-generated response for email ID {email_data.get('id', 'N/A')}:\n{generated_response}")

    # 3. Simulate human review
    final_response = review_email(email_data, generated_response)
    
    # Check if the human review changed the response
    if final_response != generated_response:
        logger.info(f"Human modified response for email ID {email_data.get('id', 'N/A')}:\n{final_response}")
    else:
        logger.info(f"Human approved AI-generated response for email ID {email_data.get('id', 'N/A')} without changes.")

    # 4. Attempt to send the final email
    # Construct a dictionary suitable for send_email
    email_to_send = {
        "to": email_data.get("from"), # Reply to the sender of the original email
        "subject": f"Re: {email_data.get('subject', '')}",
        "body": final_response # The full formatted email including greeting and signature
    }

    logger.info(f"Attempting to send final email for ID {email_data.get('id', 'N/A')} to {email_to_send['to']}...")
    # NOTE: send_email expects 'test_email' which has 'response' field.
    # You might need to adjust send_email to accept 'body' directly.
    # For now, let's adapt to what send_email expects if it's the exact structure:
    # It might be simpler to change `send_email` to take `to`, `subject`, `body` directly.
    # Assuming `send_email` takes email_to_send and user_name:
    if send_email(email_to_send, your_company_name): # Or 'EMAIL_USERNAME' if send_email needs the full address
        print(f"Email ID {email_data.get('id', 'N/A')} sent successfully.")
        logger.info(f"Email ID {email_data.get('id', 'N/A')} sent successfully.")
    else:
        print(f"Failed to send email ID {email_data.get('id', 'N/A')}.")
        logger.warning(f"Failed to send email ID {email_data.get('id', 'N/A')}.")


if __name__ == "__main__":
    # Load your JSON email samples
    # Assuming your JSON data is in a file named 'email_samples.json'
    try:
        with open('email_samples.json', 'r') as f:
            email_samples = json.load(f)
    except FileNotFoundError:
        print("Error: 'email_samples.json' not found. Please create it with your email data.")
        email_samples = [] # Provide an empty list to prevent further errors

    # Choose an email from the samples to test
    # Example: Test email ID 13 (Damaged Goods in Order 95479 from james.liu)
    # This will now use "James" for the greeting and "shipcube" for the signature.
    test_email_id = 13
    selected_email = next((email for email in email_samples if email["id"] == str(test_email_id)), None)

    if selected_email:
        run_test_email_response_flow(selected_email)
    else:
        print(f"Email with ID {test_email_id} not found in samples.")

    # You can loop through all emails or pick different ones for testing:
