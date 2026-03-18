from src.orcherstration_recommender.state import State


def intent_combination_node(state: State) -> State:
    """
    Intent Extraction — Node 5 | Intent Combination
    Algo pur, 0 LLM.
    Reads  : detected_layers, detected_category, detected_requirements,
             detected_metrics_filters, detected_used_orchestrators, db_vocabulary
    Writes : intent_json
    """
    try:
        db_vocabulary            = state.get("db_vocabulary", {})
        detected_requirements    = state.get("detected_requirements", [])
        detected_metrics_filters = state.get("detected_metrics_filters", [])
        criteria_list            = db_vocabulary.get("criterion", [])

        # ── Construire le mapping exact depuis la DB ──────────────────
        # Prioriser la version avec majuscule initiale
        criteria_exact = {}
        for c in criteria_list:
            key = c.lower()
            if key not in criteria_exact or c[0].isupper():
                criteria_exact[key] = c

        # ── Normaliser les requirements vers les noms exacts de la DB ─
        normalized_requirements = []
        for req in detected_requirements:
            # 1. Normalisation exacte
            match = criteria_exact.get(req.lower())
            if match:
                normalized_requirements.append(match)
            else:
                # 2. Normalisation par inclusion
                partial_match = next(
                    (c for c in criteria_list if req.lower() in c.lower()),
                    None
                )
                if partial_match:
                    normalized_requirements.append(partial_match)
                else:
                    normalized_requirements.append(req)

        print(f"\n[DEBUG normalized_requirements]: {normalized_requirements}")

        intent_json = {
            "layers":             state.get("detected_layers", []),
            "category":           state.get("detected_category", None),
            "requirements":       normalized_requirements,
            "metrics_filters":    detected_metrics_filters,
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
