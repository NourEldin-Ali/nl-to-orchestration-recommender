from src.orcherstration_recommender.state import State


def after_cypher_query_execution(state: State) -> str:
    """
    Edge 4 — after cypher_query_execution_node
    If minimal_subgraph is empty AND attempt_try == 1
        → composition_requirement_explanation_node
    Else
        → intent_coverage_verifier_node
    """
    minimal_subgraph = state.get("minimal_subgraph", [])
    attempt_try      = state.get("attempt_try", 1)

    if not minimal_subgraph and attempt_try == 1:
        return "composition_requirement_explanation"
    return "intent_coverage_verifier"


def after_intent_graph_update(state: State) -> str:
    """
    Edge 6 — after intent_graph_update_node
    If composition_not_allowed → END
    Else → cypher_query_generation_node (re-run with updated policy)
    """
    recommendation_policy = state.get("recommendation_policy", "composition_not_allowed")

    if recommendation_policy == "composition_not_allowed":
        return "end"
    return "cypher_query_generation"