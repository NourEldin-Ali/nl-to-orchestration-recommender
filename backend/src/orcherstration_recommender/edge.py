from src.orcherstration_recommender.state import State


def after_start(
    state: State,
    one_step: bool = False,
    based_on_existing_orchestrator: bool = False,
) -> str:
    """
    Edge 0 - after START.

    Priority:
    1. based_on_existing_orchestrator -> load db schema/vocabulary first
    2. one_step -> direct baseline
    3. default -> full graph
    """
    use_one_step = state.get("one_step", one_step)
    use_based_on_existing = state.get(
        "based_on_existing_orchestrator",
        based_on_existing_orchestrator,
    )

    if use_based_on_existing:
        return "db_schema_discovery"
    if use_one_step:
        return "recommandantion_baseline"
    return "db_schema_discovery"


def after_db_vocabulary(
    state: State,
    based_on_existing_orchestrator: bool = False,
) -> str:
    """
    Edge 1 - after db_vocabulary.

    If based_on_existing_orchestrator is enabled, extract the already used
    orchestrator before calling the baseline node. Otherwise continue with the
    full extraction pipeline.
    """
    use_based_on_existing = state.get(
        "based_on_existing_orchestrator",
        based_on_existing_orchestrator,
    )
    if use_based_on_existing:
        return "used_orchestrators_extraction"
    return "layer_extraction"


def after_used_orchestrators_extraction(
    state: State,
    based_on_existing_orchestrator: bool = False,
) -> str:
    """
    Edge 2 - after used_orchestrators_extraction.

    The baseline-existing mode stops here and hands the extracted existing
    orchestrator(s) to the baseline node. The full graph continues to
    intent_combination.
    """
    use_based_on_existing = state.get(
        "based_on_existing_orchestrator",
        based_on_existing_orchestrator,
    )
    if use_based_on_existing:
        return "recommandantion_baseline"
    return "intent_combination"


def after_cypher_query_execution(state: State) -> str:
    """
    Edge 4 - after cypher_query_execution_node.
    If minimal_subgraph is empty AND attempt_try == 1
        -> composition_requirement_explanation_node
    Else
        -> intent_coverage_verifier_node
    """
    minimal_subgraph = state.get("minimal_subgraph", [])
    attempt_try = state.get("attempt_try", 1)

    if not minimal_subgraph and attempt_try == 1:
        return "composition_requirement_explanation"
    return "intent_coverage_verifier"


def after_intent_graph_update(state: State) -> str:
    """
    Edge 6 - after intent_graph_update_node.
    If composition_not_allowed -> END
    Else -> cypher_query_generation_node (re-run with updated policy)
    """
    recommendation_policy = state.get("recommendation_policy", "composition_not_allowed")

    if recommendation_policy == "composition_not_allowed":
        return "end"
    return "cypher_query_generation"
