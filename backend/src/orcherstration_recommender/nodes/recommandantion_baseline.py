import json

from langchain_core.messages import SystemMessage

from src.orcherstration_recommender.prompts.recommandantion_baseline import (
    RECOMMENDATION_BASELINE_PROMPT,
)
from src.orcherstration_recommender.state import State
from src.orcherstration_recommender.token_usage import add_token_usage


def recommandantion_baseline(state: State, llm) -> State:
    """
    Baseline recommendation node.

    In the generic one-step mode it uses only the user query. In the
    based-on-existing-orchestrator mode it also receives the vocabulary-backed
    orchestrator list and the extracted already-used orchestrator(s).
    """
    user_query = state.get("user_query", "")
    db_vocabulary = state.get("db_vocabulary", {})
    available_orchestrators = db_vocabulary.get("orchestrators", [])
    detected_used_orchestrators = state.get("detected_used_orchestrators", [])
    available_orchestrators_payload = (
        json.dumps(available_orchestrators, indent=2)
        if available_orchestrators
        else "Not provided"
    )
    detected_used_orchestrators_payload = (
        json.dumps(detected_used_orchestrators, indent=2)
        if detected_used_orchestrators
        else "None detected"
    )

    messages = [
        SystemMessage(
            content=RECOMMENDATION_BASELINE_PROMPT.format(
                user_query=user_query,
                available_orchestrators=available_orchestrators_payload,
                detected_used_orchestrators=detected_used_orchestrators_payload,
            )
        )
    ]

    try:
        response = llm.invoke(messages)
        response_draft = response.content.strip()

        return {
            "final_recommendation": response_draft,
            "final_response": response_draft,
            "response_draft": response_draft,
            "status": "done",
            "token_usage": add_token_usage(state, response, "recommandantion_baseline"),
        }

    except Exception as e:
        return {
            "errors": state.get("errors", []) + [f"recommandantion_baseline: {e}"],
            "status": "failed",
        }
