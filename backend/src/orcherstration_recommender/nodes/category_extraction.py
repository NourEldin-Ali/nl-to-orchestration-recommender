import json
from src.orcherstration_recommender.state import State
from src.orcherstration_recommender.prompts.prompts_list import CATEGORY_EXTRACTION_PROMPT
from src.orcherstration_recommender.token_usage import add_token_usage
from langchain_core.messages import SystemMessage


def category_extraction_node(state: State, llm) -> State:
    """
    Intent Extraction — Node 2 | Category Extraction
    Reads  : user_query, db_vocabulary, detected_layers
    Writes : detected_category
    """
    user_query      = state.get("user_query", "")
    db_vocabulary   = state.get("db_vocabulary", {})
    detected_layers = state.get("detected_layers", [])
    categories      = db_vocabulary.get("categories", [])

    messages = [
        SystemMessage(content=CATEGORY_EXTRACTION_PROMPT.format(
            user_query=user_query,
            detected_layers=json.dumps(detected_layers),
            categories=json.dumps(categories, indent=2),
        ))
    ]

    try:
        response = llm.invoke(messages)
        raw = response.content.strip()

        if raw.startswith("```json"):
            raw = raw[7:]
        elif raw.startswith("```"):
            raw = raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()

        result = json.loads(raw)
        detected_category = result.get("category", None)

        print(f"\n[DEBUG detected_category]: {detected_category}")

        return {
            "detected_category": detected_category,
            "status":            "running",
            "token_usage":       add_token_usage(state, response, "category_extraction"),
        }

    except Exception as e:
        return {
            "errors": state.get("errors", []) + [f"category_extraction_node: {e}"],
            "status": "failed",
        }
