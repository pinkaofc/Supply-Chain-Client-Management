from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from utils.formatter import clean_text
from config import GEMINI_API_KEY
from utils.logger import get_logger

logger = get_logger(__name__)

def summarize_email(email: dict) -> str:
    """
    Uses Gemini to generate a concise summary of the email content.

    Arguments:
        email (dict): The email to be summarized. Expected key: "body".

    Returns:
        str: A cleaned summary string.
    """
    prompt_template = PromptTemplate(
        input_variables=["content"],
        template="Summarize the following email content in 2 to 3 sentences: {content}"
    )

    prompt = prompt_template.format(content=email.get("body", ""))

    model = ChatGoogleGenerativeAI(
        model="gemini-2.5-pro",
        temperature=0.5,
        google_api_key=GEMINI_API_KEY
    )

    try:
        summary_result_obj = model.invoke(prompt)
        summary_text = clean_text(summary_result_obj.content).strip()
        logger.debug("Raw summary output: %s", summary_text)
    except Exception as e:
        error_message = str(e).lower()
        logger.error("Gemini API error in summarize_email: %s", error_message)
        if "quota" in error_message or "429" in error_message:
            raise RuntimeError("Gemini quota exceeded")
        summary_text = f"Summary generation failed: {str(e)}"

    return summary_text