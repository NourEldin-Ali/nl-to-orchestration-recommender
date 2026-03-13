from src.orcherstration_recommender.state import State


def intent_combination_node(state: State) -> State:
    """
    Intent Extraction — Node 5 | Intent Combination
    Algo pur, 0 LLM.
    Reads  : detected_layers, detected_category, detected_requirements, detected_used_orchestrators
    Writes : intent_json
    """
    try:
        intent_json = {
            "layers":             state.get("detected_layers", []),
            "category":           state.get("detected_category", None),
            "requirements":       state.get("detected_requirements", []),
            "used_orchestrators": state.get("detected_used_orchestrators", []),
        }

        print(f"\n[DEBUG intent_json]: {intent_json}")

        return {
            "intent_json": intent_json,
            "status":      "running",
        }

    except Exception as e:
        return {
            "errors": state.get("errors", []) + [f"intent_combination_node: {e}"],
            "status": "failed",
        }
