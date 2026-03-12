from src.orcherstration_recommender.prompts.recommandantion_baseline import RECOMMENDATION_BASELINE_PROMPT
from src.orcherstration_recommender.state import State
from src.orcherstration_recommender.token_usage import add_token_usage
from langchain_core.messages import SystemMessage

def recommandantion_baseline(state: State, llm) -> State:
    """
    
    """
    user_query = state.get("user_query", "")

    messages = [
        SystemMessage(
            content=RECOMMENDATION_BASELINE_PROMPT.format(user_query=user_query)
        )
    ]

    try:
        response = llm.invoke(messages)
        response_draft = response.content.strip()

        return {
            "final_recommendation": response_draft,
            "final_response": response_draft,
            "status": "done",
            "token_usage": add_token_usage(state, response, "recommandantion_baseline"),
        }

    except Exception as e:
        return {
            "errors": state.get("errors", []) + [f"recommandantion_baseline: {e}"],
            "status": "failed",
        }
