from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from utils.logger import get_logger
from utils.formatter import clean_text, format_email
from config import GEMINI_API_KEY

logger = get_logger(__name__)

def generate_response(email: dict, summary: str, recipient_name: str, your_name: str) -> str:
    """
    Generates a formal email response using Gemini.
    This function now expects Gemini to produce *only the body* of the email.
    """
    prompt_template = PromptTemplate(
        input_variables=["recipient_name", "subject", "content", "summary", "your_name"],
        template=(
            "You are an email assistant named {your_name}. "
            "Based on the following email details and summary, "
            "generate only the **core body content** for a formal email response to {recipient_name}. "
            "**Absolutely do not include a subject line, any form of greeting (e.g., 'Hi [Name],', 'Hello,'), or any closing signature (e.g., 'Best regards, [Your Name]', 'Sincerely').** "
            "Focus only on the main message. \n\n"
            "Original Email Details:\n"
            "From: {recipient_name}\n"
            "Subject: {subject}\n"
            "Content: {content}\n"
            "Summary: {summary}\n\n"
            "Generate only the email body:\n"
        )
    )

    prompt = prompt_template.format(
        recipient_name=recipient_name,
        subject=email.get("subject", ""),
        content=email.get("body", ""),
        summary=summary,
        your_name=your_name
    )

    model = ChatGoogleGenerativeAI(
        model="gemini-2.5-pro",
        temperature=0.7,
        google_api_key=GEMINI_API_KEY
    )

    try:
        response_obj = model.invoke(prompt)
        response_text = clean_text(response_obj.content).strip()
        logger.debug("Raw response output (body only from LLM): %s", response_text)
    except Exception as e:
        error_message = str(e).lower()
        logger.error("Gemini API error in generate_response: %s", error_message)
        if "quota" in error_message or "429" in error_message:
            raise RuntimeError("Gemini quota exceeded")
        return "Error generating response."

    formatted_response = format_email(
        subject=email.get("subject", ""),
        recipient_name=recipient_name,
        body=response_text,
        user_name=your_name
    )

    return formatted_response.strip()