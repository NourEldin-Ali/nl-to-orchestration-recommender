from src.orcherstration_recommender.state import State
from src.orcherstration_recommender.prompts.prompts_list import COMPOSITION_EXPLANATION_PROMPT
from langchain_core.messages import SystemMessage

def composition_requirement_explanation_node(state: State, llm) -> State:
    """
    Component 1 — SLM | Composition Requirement Explanation
    Triggered when minimal_subgraph is empty.
    Reads  : user_query, intent_json
    Writes : response_draft (explanation to user), status (waiting_human)
    """
    user_query = state.get("user_query", "")

    messages = [
        SystemMessage(
            content=COMPOSITION_EXPLANATION_PROMPT.format(user_query=user_query)
        )
    ]

    try:
        response = llm.invoke(messages)
        response_draft = response.content.strip()

        return {
            "response_draft": response_draft,
            "status": "waiting_human",
        }

    except Exception as e:
        return {
            "errors": state.get("errors", []) + [f"composition_requirement_explanation_node: {e}"],
            "status": "failed",
        }