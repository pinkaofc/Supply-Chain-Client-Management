from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from config import GEMINI_API_KEY
from utils.logger import get_logger
from utils.formatter import clean_text

logger = get_logger(__name__)

def filter_email(email: dict) -> str:
    """
    Uses Gemini to analyze the email and classify its sentiment.
    Sentiment is one of: 'positive', 'neutral', or 'negative'.
    """
    prompt_template = PromptTemplate(
        input_variables=["subject", "content"],
        template=(
            "Based on the following email, classify its overall sentiment as 'positive', 'neutral', or 'negative'. "
            "Respond with only the sentiment label, nothing else.\n\n"
            "Subject: {subject}\n"
            "Content: {content}\n"
            "Sentiment:"
        )
    )

    prompt = prompt_template.format(
        subject=email.get("subject", ""),
        content=email.get("body", "")
    )

    model = ChatGoogleGenerativeAI(
        model="gemini-2.5-pro",
        temperature=0.0,
        google_api_key=GEMINI_API_KEY
    )

    try:
        sentiment_result = model.invoke(prompt)
        sentiment_text = clean_text(sentiment_result.content).strip().lower()
        logger.debug("Raw sentiment output: %s", sentiment_text)
    except Exception as e:
        error_message = str(e).lower()
        logger.error("Gemini API error in filter_email: %s", error_message)
        if "quota" in error_message or "429" in error_message:
            raise RuntimeError("Gemini quota exceeded")
        return "unknown"

    if sentiment_text in ["positive", "neutral", "negative"]:
        return sentiment_text
    else:
        logger.warning("Gemini returned unexpected sentiment in filter_email: '%s'. Returning 'unknown'.", sentiment_text)
        return "unknown"