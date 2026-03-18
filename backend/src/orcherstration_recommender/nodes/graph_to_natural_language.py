import json
from src.orcherstration_recommender.state import State
from src.orcherstration_recommender.prompts.prompts_list import GRAPH_TO_NL_PROMPT
from src.orcherstration_recommender.token_usage import add_token_usage
from langchain_core.messages import SystemMessage


def graph_to_natural_language_node(state: State, llm) -> State:
    """
    Component 1 — SLM | Graph-to-Natural-Language Transformation
    Pure structural transformation — no reasoning or inference.
    Reads  : coverage_annotated_intent, enriched_subgraph
    Writes : response_draft (evidence-based draft in natural language)
    """
    coverage_annotated_intent = state.get("coverage_annotated_intent", {})
    enriched_subgraph         = state.get("enriched_subgraph", [])

    messages = [
        SystemMessage(
            content=GRAPH_TO_NL_PROMPT.format(
                coverage_annotated_intent=json.dumps(coverage_annotated_intent, indent=2),
                enriched_subgraph=json.dumps(enriched_subgraph, indent=2),
            )
        )
    ]

    try:
        response = llm.invoke(messages)
        response_draft = response.content.strip()

        print(f"\n[DEBUG response_draft]:\n{response_draft}")

        return {
            "response_draft": response_draft,
            "status":         "running",
            "token_usage":    add_token_usage(state, response, "graph_to_natural_language"),
        }

    except Exception as e:
        return {
            "errors": state.get("errors", []) + [f"graph_to_natural_language_node: {e}"],
            "status": "failed",
        }
