from jinja2 import Template 

def clean_text(text: str) -> str:
    """
    Removes extra whitespace and unwanted newlines from text.
    """
    # Using .split() with no arguments splits by any whitespace and removes empty strings,
    # then " ".join() puts a single space between each word. This is effective.
    return " ".join(text.split()).strip()

def format_email(subject: str, recipient_name: str, body: str, user_name: str) -> str:
    """
    Formats an email reply with a clean structure, avoiding duplicate headers or signatures.

    Arguments:
        subject (str): Subject of the original email.
        recipient_name (str): Name or email of the person you're replying to (e.g., "james.liu@..." or "Pinka").
        body (str): AI-generated response body.
        user_name (str): Your name to be used in the signature (e.g., "shipcube").

    Returns:
        str: A formatted email string.
    """
    cleaned_subject = clean_text(subject)
    
    # --- Logic to derive a friendly recipient name for the greeting ---
    # This tries to be smart about extracting a first name from an email address
    # If recipient_name is "james.liu@fasttrackglobal.cn", this will become "James"
    # If recipient_name is "Pinka", this will become "Pinka"
    # If it's something like "itsprianka1230@gmail.com", it becomes "Itsprianka1230"
    # You might need to refine this further if you have specific alias mappings.
    friendly_recipient_name = "Customer" # Default fallback
    if "@" in recipient_name:
        local_part = recipient_name.split('@')[0]
        # Try to get the first part if there's a dot, otherwise just capitalize
        if "." in local_part:
            friendly_recipient_name = local_part.split('.')[0].capitalize()
        else:
            friendly_recipient_name = local_part.capitalize()
    elif recipient_name: # If it's already a name like "Pinka"
        friendly_recipient_name = recipient_name.capitalize()
    # -----------------------------------------------------------------

    cleaned_user = clean_text(user_name)
    cleaned_body = body.strip()

    # --- Aggressively clean LLM output to remove unintended greetings ---
    greeting_starters = ["hi", "hello", "dear", "good morning", "good afternoon", "good evening"]
    lines = cleaned_body.splitlines()
    if lines:
        first_line = lines[0].strip().lower()
        # Check if the first line starts with a greeting phrase and likely ends with a comma
        if any(first_line.startswith(phrase) for phrase in greeting_starters) and (first_line.endswith(',') or ' ' in first_line):
            temp_body_lines = lines[1:]
            # Remove any immediate empty lines after the greeting
            while temp_body_lines and not temp_body_lines[0].strip():
                temp_body_lines.pop(0)
            cleaned_body = "\n".join(temp_body_lines).strip()

    # --- Aggressively clean LLM output to remove unintended signatures ---
    signature_phrases = ["best regards,", "sincerely,", "thank you,", "regards,"]
    body_lines = cleaned_body.splitlines()
    while body_lines:
        last_line = body_lines[-1].strip().lower()
        
        # Check if the last line (or previous lines) looks like a signature
        is_signature = False
        if any(last_line.startswith(phrase) for phrase in signature_phrases):
            is_signature = True
        elif last_line == cleaned_user.lower(): # Check if it's just the user_name (e.g., "shipcube")
            is_signature = True
        
        # Also check for "Your Name" or "Company Name" if LLM generates it
        elif f"{cleaned_user.lower()}" in last_line and (any(phrase in last_line for phrase in signature_phrases) or len(last_line.split()) < 4): # heuristic
             is_signature = True

        if is_signature:
            body_lines.pop() # Remove the signature line
            # Also remove any preceding empty lines that were part of the signature block
            while body_lines and not body_lines[-1].strip():
                body_lines.pop()
        else:
            break # Stop if no signature-like line is found

    cleaned_body = "\n".join(body_lines).strip()
    # -----------------------------------------------------------------

    formatted_email = (
        f"Subject: Re: {cleaned_subject}\n\n"
        f"Hi {friendly_recipient_name},\n\n"
        f"{cleaned_body}\n\n"
        f"Best regards,\n"
        f"{cleaned_user}"
    )

    return formatted_email