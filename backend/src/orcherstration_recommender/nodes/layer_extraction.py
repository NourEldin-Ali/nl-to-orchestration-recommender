import json
from src.orcherstration_recommender.state import State
from src.orcherstration_recommender.prompts.prompts_list import LAYER_EXTRACTION_PROMPT
from src.orcherstration_recommender.token_usage import add_token_usage
from langchain_core.messages import SystemMessage


def layer_extraction_node(state: State, llm) -> State:
    """
    Intent Extraction — Node 1 | Layer Extraction
    Reads  : user_query, db_vocabulary
    Writes : detected_layers
    """
    user_query   = state.get("user_query", "")
    db_vocabulary = state.get("db_vocabulary", {})
    layers       = db_vocabulary.get("layers", [])

    messages = [
        SystemMessage(content=LAYER_EXTRACTION_PROMPT.format(
            user_query=user_query,
            layers=json.dumps(layers, indent=2),
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
        detected_layers = result.get("layers", [])

        print(f"\n[DEBUG detected_layers]: {detected_layers}")

        return {
            "detected_layers": detected_layers,
            "status":          "running",
            "token_usage":     add_token_usage(state, response, "layer_extraction"),
        }

    except Exception as e:
        return {
            "errors": state.get("errors", []) + [f"layer_extraction_node: {e}"],
            "status": "failed",
        }
