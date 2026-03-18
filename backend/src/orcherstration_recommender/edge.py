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

    print(f"\n[DEBUG after_cypher_query_execution]:")
    print(f"  minimal_subgraph length : {len(minimal_subgraph)}")
    print(f"  minimal_subgraph        : {minimal_subgraph}")
    print(f"  attempt_try             : {attempt_try}")

    if not minimal_subgraph and attempt_try == 1:
        return "composition_requirement_explanation"
    return "intent_coverage_verifier"


def after_intent_graph_update(state: State) -> str:
    """
    Edge 6 — after intent_graph_update_node
    If composition_not_allowed → intent_coverage_verifier (coverage gap explanation)
    Else → cypher_query_generation_node (re-run with updated policy)
    """
    recommendation_policy = state.get("recommendation_policy", "composition_not_allowed")

    print(f"\n[DEBUG after_intent_graph_update]:")
    print(f"  recommendation_policy : {recommendation_policy}")

    if recommendation_policy == "composition_not_allowed":
        return "intent_coverage_verifier"
    return "cypher_query_generation"