from src.orcherstration_recommender.state import State
from src.orcherstration_recommender.prompts.prompts_list import JUSTIFIED_RECOMMENDATION_PROMPT, COVERAGE_GAP_EXPLANATION_PROMPT
from src.orcherstration_recommender.token_usage import add_token_usage
from langchain_core.messages import SystemMessage


def intent_aligned_justification_node(state: State, llm) -> State:
    """
    Component 1 — SLM | Intent-Aligned Justification
    Reads  : response_draft, coverage, final_recommendation, user_query
    Writes : final_response
             - If coverage FULL                → justified recommendation response
             - If final_recommendation is CompositionOfTools → justified recommendation response
               (composition case: PARTIAL coverage is expected and normal)
             - If coverage PARTIAL | NONE (and not CompositionOfTools) → coverage-gap explanation response
    """
    user_query           = state.get("user_query", "")
    response_draft       = state.get("response_draft", "")
    coverage             = state.get("coverage", "NONE")
    final_recommendation = state.get("final_recommendation", "None")

    # ── Select prompt based on coverage and final_recommendation ─────
    # CompositionOfTools: PARTIAL coverage is expected and normal —
    # each tool covers a subset; collectively they satisfy the intent.
    # → use the justified recommendation prompt, not the gap explanation.
    if coverage == "FULL" or final_recommendation == "CompositionOfTools":
        prompt = JUSTIFIED_RECOMMENDATION_PROMPT.format(
            user_query=user_query,
            response_draft=response_draft,
        )
    else:
        prompt = COVERAGE_GAP_EXPLANATION_PROMPT.format(
            user_query=user_query,
            response_draft=response_draft,
            coverage=coverage,
        )

    response = llm.invoke([SystemMessage(content=prompt)])

    return {
        "final_response": response.content.strip(),
        "status":         "done",
        "token_usage":    add_token_usage(state, response, "intent_aligned_justification"),
    }
