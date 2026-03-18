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

    layers          = intent_json.get("layers", [])
    category        = intent_json.get("category", "")
    requirements    = intent_json.get("requirements", [])
    metrics_filters = intent_json.get("metrics_filters", [])

    if isinstance(layers, str):
        layers = [layers]

    # ── Extraire les relations depuis db_schema ───────────────────────
    relations = _extract_relations(db_schema)

    print(f"\n[DEBUG intent_coverage_verifier]:")
    print(f"  relations        : {relations}")
    print(f"  layers           : {layers}")
    print(f"  category         : {category}")
    print(f"  requirements     : {requirements}")
    print(f"  metrics_filters  : {metrics_filters}")
    print(f"  enriched_subgraph length: {len(enriched_subgraph)}")
    if enriched_subgraph:
        print(f"  first orchestrator keys: {list(enriched_subgraph[0].keys())}")
        print(f"  first orchestrator     : {enriched_subgraph[0]}")

    try:
        # ── Step 1 : Annotate coverage ────────────────────────────────
        coverage_annotated_intent, satisfied_count, total_count = _annotate_coverage(
            layers=layers,
            category=category,
            requirements=requirements,
            metrics_filters=metrics_filters,
            enriched_subgraph=enriched_subgraph,
            relations=relations,
        )

        print(f"\n[DEBUG coverage_annotation]:")
        print(f"  satisfied_count : {satisfied_count}")
        print(f"  total_count     : {total_count}")
        print(f"  annotations     : {coverage_annotated_intent}")

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

        print(f"\n[DEBUG coverage]             : {coverage}")
        print(f"[DEBUG final_recommendation] : {final_recommendation}")

        # ── Step 4 : Update Intent node in Neo4j ──────────────────────
        _update_intent_node(
            intent_id=intent_id,
            coverage=coverage,
            final_recommendation=final_recommendation,
        )

        return {
            "coverage_annotated_intent": {
                **coverage_annotated_intent,
                "coverage":             coverage,
                "final_recommendation": final_recommendation,
            },
            "coverage":             coverage,
            "final_recommendation": final_recommendation,
            "status":               "running",
        }

    except Exception as e:
        print(f"\n[DEBUG intent_coverage_verifier ERROR]: {e}")
        return {
            "errors": state.get("errors", []) + [f"intent_coverage_verifier_node: {e}"],
            "status": "failed",
        }


def _extract_relations(db_schema: list) -> dict:
    relations = {}
    for entry in db_schema:
        if entry.get("from") == "Orchestrator":
            rel   = entry.get("relation", "")
            to    = entry.get("to", "")
            props = entry.get("relation_properties", [])

            if to == "Layer":
                relations["covers"] = rel
            elif to == "Category":
                relations["has_category"] = rel
            elif to == "Orchestrator":
                relations["based_on"] = rel
            elif to == "Criterion":
                if "value" in props:
                    relations["has_metrics"] = rel
                else:
                    relations["supports"] = rel

    return relations


def _annotate_coverage(
    layers: list,
    category: str,
    requirements: list,
    metrics_filters: list,
    enriched_subgraph: list,
    relations: dict,
) -> tuple:
    covers_rel       = relations.get("covers", "COVERS").lower()
    has_category_rel = relations.get("has_category", "HAS_CATEGORY").lower()
    supports_rel     = relations.get("supports", "SUPPORTS").lower()
    has_metrics_rel  = relations.get("has_metrics", "HAS_METRICS").lower()

    print(f"\n[DEBUG _annotate_coverage]:")
    print(f"  covers_rel       : {covers_rel}")
    print(f"  has_category_rel : {has_category_rel}")
    print(f"  supports_rel     : {supports_rel}")
    print(f"  has_metrics_rel  : {has_metrics_rel}")

    # ── Collecter les valeurs présentes dans le subgraph ──────────────
    subgraph_layers     = set()
    subgraph_categories = set()
    subgraph_criteria   = set()
    subgraph_metrics    = {}

    for orchestrator in enriched_subgraph:
        for l in orchestrator.get(covers_rel, []):
            subgraph_layers.add(l.get("name", "").lower())
        for c in orchestrator.get(has_category_rel, []):
            subgraph_categories.add(c.get("name", "").lower())
        for cr in orchestrator.get(supports_rel, []):
            subgraph_criteria.add(cr.get("name", "").lower())
        for m in orchestrator.get(has_metrics_rel, []):
            name  = m.get("name", "").lower()
            value = m.get("value")
            if name not in subgraph_metrics:
                subgraph_metrics[name] = []
            if value is not None:
                subgraph_metrics[name].append(value)

    print(f"  subgraph_layers     : {subgraph_layers}")
    print(f"  subgraph_categories : {subgraph_categories}")
    print(f"  subgraph_criteria   : {subgraph_criteria}")
    print(f"  subgraph_metrics    : {subgraph_metrics}")

    annotations     = []
    satisfied_count = 0
    total_count     = 0

    # ── Annotate COVERS ───────────────────────────────────────────────
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

    # ── Annotate HAS_CATEGORY ─────────────────────────────────────────
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

    # ── Annotate REQUIRES ─────────────────────────────────────────────
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

    # ── Annotate METRICS FILTERS ──────────────────────────────────────
    for mf in metrics_filters:
        criterion_name = mf.get("criterion_name", "").lower()
        operator       = mf.get("operator", "")
        values_list    = subgraph_metrics.get(criterion_name, [])
        satisfied      = False

        if operator == ">=" and values_list:
            threshold = mf.get("value")
            satisfied = any(
                _safe_int(v) >= threshold
                for v in values_list
                if _safe_int(v) is not None
            )

        elif operator == "<=" and values_list:
            threshold = mf.get("value")
            satisfied = any(
                _safe_int(v) <= threshold
                for v in values_list
                if _safe_int(v) is not None
            )

        elif operator == "==" and values_list:
            value = str(mf.get("value", "")).lower()
            satisfied = any(str(v).lower() == value for v in values_list)

        elif operator == "contains_any" and values_list:
            expected = [str(v).lower() for v in mf.get("values", [])]
            satisfied = any(
                any(e in str(v).lower() for e in expected)
                for v in values_list
            )

        annotations.append({
            "relation":  "METRICS_FILTER",
            "value":     criterion_name,
            "operator":  operator,
            "satisfied": satisfied,
        })
        total_count += 1
        if satisfied:
            satisfied_count += 1

    coverage_annotated_intent = {"annotations": annotations}
    return coverage_annotated_intent, satisfied_count, total_count


def _safe_int(value) -> int:
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


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