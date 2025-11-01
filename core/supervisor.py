from langgraph.graph import START, END, StateGraph
from agents import filtering_agent, summarization_agent, response_agent, human_review_agent
from core.state import EmailState
from utils.logger import get_logger
from functools import partial
from datetime import datetime

logger = get_logger(__name__)

# --- LangGraph Nodes ---

def filter_node(state: EmailState) -> EmailState:
    email_data = state.current_email
    email_id = email_data.get('id', 'N/A')
    logger.info(f"[Filtering] Started for email ID: {email_id}")
    try:
        classification = filtering_agent.filter_email(email_data)
        logger.info(f"[Filtering] Completed for ID {email_id} with classification: {classification}")
        state.classification = classification
        state.metadata[email_id] = state.metadata.get(email_id, {})
        state.metadata[email_id]["classification"] = classification
        state.processing_error = None
    except Exception as e:
        logger.error(f"[Filtering] Error for email ID {email_id}: {e}", exc_info=True)
        state.classification = "unknown"
        state.metadata[email_id] = state.metadata.get(email_id, {})
        state.metadata[email_id]["classification"] = "error_during_filtering"
        state.processing_error = f"Filtering failed: {str(e)}"
    return state

def summarize_node(state: EmailState) -> EmailState:
    email_data = state.current_email
    email_id = email_data.get('id', 'N/A')
    logger.info(f"[Summarization] Started for email ID: {email_id}")
    try:
        if state.classification == "spam" or state.processing_error:
            state.summary = "Summary skipped due to classification or previous error."
            logger.info(f"[Summarization] Skipped for email ID: {email_id}")
        else:
            summary = summarization_agent.summarize_email(email_data)
            logger.info(f"[Summarization] Completed for ID: {email_id}")
            state.summary = summary
            state.metadata[email_id]["summary"] = summary
            state.processing_error = None
    except Exception as e:
        logger.error(f"[Summarization] Error for email ID {email_id}: {e}", exc_info=True)
        state.summary = "Summary generation failed."
        state.metadata[email_id]["summary"] = "error_during_summarization"
        state.processing_error = f"Summarization failed: {str(e)}"
    return state

def respond_node(state: EmailState, your_name: str, recipient_name: str) -> EmailState:
    email_data = state.current_email
    email_id = email_data.get('id', 'N/A')
    email_summary = state.summary
    logger.info(f"[Response] Started for email ID: {email_id}")

    if state.classification in ["spam", "promotional"] or state.processing_error:
        state.generated_response_body = "Not applicable. Email skipped or failed previous step."
        state.metadata[email_id]["response_status"] = "skipped"
        logger.info(f"[Response] Skipped for email ID {email_id} due to classification or previous error.")
        return state

    try:
        response_text = response_agent.generate_response(
            email=email_data,
            summary=email_summary,
            recipient_name=recipient_name,
            your_name=your_name
        )

        state.generated_response_body = response_text
        state.metadata[email_id]["raw_generated_response"] = response_text
        state.processing_error = None

        requires_review = (
            state.classification == "needs_review" or
            ("?" in response_text and state.classification != "spam")
        )
        state.requires_human_review = requires_review

        if requires_review:
            logger.info(f"[Response] Email ID {email_id} flagged for human review.")
            state.metadata[email_id]["response_status"] = "awaiting_human_review"
        else:
            state.metadata[email_id]["response_status"] = "ready_to_send"

        state.history.append({
            "email_id": email_id,
            "classification": state.classification,
            "summary": state.summary,
            "raw_response": state.generated_response_body,
            "requires_human_review": state.requires_human_review,
            "timestamp": email_data.get("timestamp") or datetime.now().isoformat()
        })
        logger.info(f"[Response] Completed for ID: {email_id}")

    except Exception as e:
        logger.error(f"[Response] Error for email ID {email_id}: {e}", exc_info=True)
        state.generated_response_body = "Response generation failed."
        state.metadata[email_id]["response_status"] = "error_during_response_generation"
        state.processing_error = f"Response generation failed: {str(e)}"
    return state

# --- Routing Logic ---

def route_after_filtering(state: EmailState) -> str:
    if state.classification in ["spam", "promotional"]:
        logger.info(f"[Supervisor] Email ID {state.current_email_id} classified as {state.classification}. Ending workflow.")
        return "end_workflow"
    elif state.processing_error:
        logger.warning(f"[Supervisor] Email ID {state.current_email_id} encountered an error during filtering. Ending workflow.")
        return "end_workflow"
    else:
        return "summarize"

# --- Supervisor LangGraph ---

def supervisor_langgraph(selected_email: dict, your_name: str, recipient_name: str) -> EmailState:
    email_id = selected_email.get("id", "N/A")

    initial_state = EmailState(
        current_email=selected_email,
        current_email_id=email_id,
        emails=[selected_email],
        metadata={email_id: {}}
    )

    workflow = StateGraph(EmailState)

    workflow.add_node("filter", filter_node)
    workflow.add_node("summarize", summarize_node)

    respond_partial_node = partial(respond_node, your_name=your_name, recipient_name=recipient_name)
    workflow.add_node("respond", respond_partial_node)

    workflow.set_entry_point("filter")

    workflow.add_conditional_edges(
        "filter",
        route_after_filtering,
        {
            "summarize": "summarize",
            "end_workflow": END
        }
    )
    workflow.add_edge("summarize", "respond")
    workflow.add_edge("respond", END)

    app = workflow.compile()

    try:
        # The output of invoke() is a dictionary, not the dataclass instance.
        final_state_dict = app.invoke(initial_state)

        # *** THE FIX: Reconstruct the EmailState object from the dictionary ***
        final_state_instance = EmailState(**final_state_dict)

    except Exception as e:
        if "quota" in str(e).lower() or "429" in str(e):
            logger.warning(f"[Supervisor] Quota exceeded for email ID {email_id}. Skipping.")
            final_state_instance = EmailState(
                current_email=selected_email,
                current_email_id=email_id,
                classification="error",
                summary="Quota exceeded.",
                generated_response_body="Gemini quota exceeded. Please retry tomorrow or upgrade your plan.",
                processing_error="Quota exceeded"
            )
        else:
            logger.critical(f"[Supervisor] CRITICAL ERROR during LangGraph invocation for email ID {email_id}: {e}", exc_info=True)
            final_state_instance = EmailState(
                current_email=selected_email,
                current_email_id=email_id,
                classification="error",
                summary="LangGraph invocation failed.",
                generated_response_body="Error during workflow execution.",
                processing_error=f"LangGraph execution failed: {str(e)}"
            )

    return final_state_instance