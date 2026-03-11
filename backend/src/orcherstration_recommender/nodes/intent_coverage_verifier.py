from src.orcherstration_recommender.state import State
from src.config.neo4j_config import Neo4jConnector


def intent_coverage_verifier_node(state: State) -> State:
    """
    Component 2 — Reasoner | Intent Coverage Verifier
    Structured code only — no LLM required (algorithmic per paper).
    Reads  : enriched_subgraph, intent_json, recommendation_policy, intent_id
    Writes : coverage_annotated_intent, coverage (FULL | PARTIAL | NONE),
             final_recommendation (SingleCandidate | MultipleCandidates | CompositionOfTools | None)
    """
    intent_json           = state.get("intent_json", {})
    enriched_subgraph     = state.get("enriched_subgraph", [])
    recommendation_policy = state.get("recommendation_policy", "single_only")
    intent_id             = state.get("intent_id", "")

    layers             = intent_json.get("layers", [])
    category           = intent_json.get("category", "")
    requirements       = intent_json.get("requirements", [])

    if isinstance(layers, str):
        layers = [layers]

    try:
        # ── Step 1 : Annotate coverage ────────────────────────────────
        coverage_annotated_intent, satisfied_count, total_count = _annotate_coverage(
            layers=layers,
            category=category,
            requirements=requirements,
            enriched_subgraph=enriched_subgraph,
        )

        # ── Step 2 : Compute coverage ratio ───────────────────────────
        if total_count == 0:
            coverage = "NONE"
        elif satisfied_count == total_count:
            coverage = "FULL"
        elif satisfied_count == 0:
            coverage = "NONE"
        else:
            coverage = "PARTIAL"

        # ── Step 3 : Determine final recommendation ───────────────────
        n = len(enriched_subgraph)
        final_recommendation = _determine_final_recommendation(
            n=n,
            recommendation_policy=recommendation_policy,
        )

        # ── Step 4 : Update Intent node in Neo4j ──────────────────────
        _update_intent_node(
            intent_id=intent_id,
            coverage=coverage,
            final_recommendation=final_recommendation,
        )

        return {
            "coverage_annotated_intent": coverage_annotated_intent,
            "coverage":                  coverage,
            "final_recommendation":      final_recommendation,
            "status":                    "running",
        }

    except Exception as e:
        return {
            "errors": state.get("errors", []) + [f"intent_coverage_verifier_node: {e}"],
            "status": "failed",
        }


def _annotate_coverage(
    layers: list,
    category: str,
    requirements: list,
    enriched_subgraph: list,
) -> tuple:
    """
    For each intent relation (COVERS, HAS_CATEGORY, REQUIRES),
    checks whether it is satisfied by at least one orchestrator
    in the enriched subgraph.
    Returns the annotated intent dict, satisfied count, and total count.
    """
    # Collect all values present in the enriched subgraph
    subgraph_layers      = set()
    subgraph_categories  = set()
    subgraph_criteria    = set()

    for orchestrator in enriched_subgraph:
        for l in orchestrator.get("layers", []):
            subgraph_layers.add(l.get("name", "").lower())
        for c in orchestrator.get("categories", []):
            subgraph_categories.add(c.get("name", "").lower())
        for cr in orchestrator.get("supported_criteria", []):
            subgraph_criteria.add(cr.get("name", "").lower())

    annotations = []
    satisfied_count = 0
    total_count = 0

    # Annotate COVERS relations
    for layer in layers:
        satisfied = layer.lower() in subgraph_layers
        annotations.append({
            "relation":  "COVERS",
            "value":     layer,
            "satisfied": satisfied,
        })
        total_count += 1
        if satisfied:
            satisfied_count += 1

    # Annotate HAS_CATEGORY relation
    if category:
        satisfied = category.lower() in subgraph_categories
        annotations.append({
            "relation":  "HAS_CATEGORY",
            "value":     category,
            "satisfied": satisfied,
        })
        total_count += 1
        if satisfied:
            satisfied_count += 1

    # Annotate REQUIRES relations
    for req in requirements:
        satisfied = req.lower() in subgraph_criteria
        annotations.append({
            "relation":  "REQUIRES",
            "value":     req,
            "satisfied": satisfied,
        })
        total_count += 1
        if satisfied:
            satisfied_count += 1

    coverage_annotated_intent = {"annotations": annotations}
    return coverage_annotated_intent, satisfied_count, total_count


def _determine_final_recommendation(
    n: int,
    recommendation_policy: str,
) -> str:
    """
    Determines the final recommendation type based on
    the number of orchestrators and the recommendation policy.
    Follows Algorithm 2 (DetermineFinalRecommendation) from the paper.
    """
    if n == 1:
        return "SingleCandidate"
    elif n > 1:
        if recommendation_policy == "single_only":
            return "MultipleCandidates"
        elif recommendation_policy == "composition_allowed":
            return "CompositionOfTools"
        else:
            return "None"
    else:
        return "None"


def _update_intent_node(
    intent_id: str,
    coverage: str,
    final_recommendation: str,
) -> None:
    """
    Updates the Intent node in Neo4j with coverage and final_recommendation.
    """
    driver = Neo4jConnector().get_driver()
    try:
        with driver.session() as session:
            session.run("""
                MATCH (i:Intent {id: $id})
                SET i.coverage             = $coverage,
                    i.final_recommendation = $final_recommendation
            """, id=intent_id, coverage=coverage, final_recommendation=final_recommendation)
    finally:
        driver.close()