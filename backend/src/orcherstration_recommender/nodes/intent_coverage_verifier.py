from src.orcherstration_recommender.state import State
from src.config.neo4j_config import Neo4jConnector


def intent_coverage_verifier_node(state: State) -> State:
    """
    Component 2 — Reasoner | Intent Coverage Verifier
    Structured code only — no LLM required.
    Reads  : enriched_subgraph, intent_json, recommendation_policy, intent_id, db_schema
    Writes : coverage_annotated_intent, coverage, final_recommendation
    """
    intent_json           = state.get("intent_json", {})
    enriched_subgraph     = state.get("enriched_subgraph", [])
    recommendation_policy = state.get("recommendation_policy", "single_only")
    intent_id             = state.get("intent_id", "")
    db_schema             = state.get("db_schema", [])

    layers       = intent_json.get("layers", [])
    category     = intent_json.get("category", "")
    requirements = intent_json.get("requirements", [])

    if isinstance(layers, str):
        layers = [layers]

    # ── Extraire les relations depuis db_schema ───────────────────────
    relations = _extract_relations(db_schema)

    try:
        # ── Step 1 : Annotate coverage ────────────────────────────────
        coverage_annotated_intent, satisfied_count, total_count = _annotate_coverage(
            layers=layers,
            category=category,
            requirements=requirements,
            enriched_subgraph=enriched_subgraph,
            relations=relations,
        )

        # ── Step 2 : Compute coverage ─────────────────────────────────
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


def _extract_relations(db_schema: list) -> dict:
    """
    Extrait depuis db_schema les relations pertinentes depuis Orchestrator.
    """
    relations = {}
    for entry in db_schema:
        if entry.get("from") == "Orchestrator":
            rel = entry.get("relation", "")
            to  = entry.get("to", "")
            if to == "Layer":
                relations["covers"] = rel
            elif to == "Category":
                relations["has_category"] = rel
            elif to == "Criterion":
                relations["supports"] = rel
    return relations


def _annotate_coverage(
    layers: list,
    category: str,
    requirements: list,
    enriched_subgraph: list,
    relations: dict,
) -> tuple:
    """
    Annote la couverture de chaque relation de l'intent
    dynamiquement depuis db_schema.
    """
    covers_rel       = relations.get("covers", "covers").lower() + "s"
    has_category_rel = relations.get("has_category", "has_category").lower() + "s"
    supports_rel     = relations.get("supports", "supports").lower() + "s"

    # Collecter les valeurs présentes dans le subgraph
    subgraph_layers     = set()
    subgraph_categories = set()
    subgraph_criteria   = set()

    for orchestrator in enriched_subgraph:
        for l in orchestrator.get(covers_rel, []):
            subgraph_layers.add(l.get("name", "").lower())
        for c in orchestrator.get(has_category_rel, []):
            subgraph_categories.add(c.get("name", "").lower())
        for cr in orchestrator.get(supports_rel, []):
            subgraph_criteria.add(cr.get("name", "").lower())

    annotations     = []
    satisfied_count = 0
    total_count     = 0

    # Annotate COVERS
    for layer in layers:
        satisfied = layer.lower() in subgraph_layers
        annotations.append({
            "relation":  relations.get("covers", "COVERS"),
            "value":     layer,
            "satisfied": satisfied,
        })
        total_count += 1
        if satisfied:
            satisfied_count += 1

    # Annotate HAS_CATEGORY
    if category:
        satisfied = category.lower() in subgraph_categories
        annotations.append({
            "relation":  relations.get("has_category", "HAS_CATEGORY"),
            "value":     category,
            "satisfied": satisfied,
        })
        total_count += 1
        if satisfied:
            satisfied_count += 1

    # Annotate REQUIRES
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