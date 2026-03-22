from src.orcherstration_recommender.state import State


def cypher_query_generation_node(state: State) -> State:
    """
    Component 2 — Reasoner | Cypher Query Generation
    Structured code only — no LLM required.
    Reads  : intent_json, recommendation_policy, db_schema
    Writes : minimal_cypher_query
    """
    intent_json           = state.get("intent_json", {})
    recommendation_policy = state.get("recommendation_policy", "single_only")
    db_schema             = state.get("db_schema", [])

    layers             = intent_json.get("layers", [])
    category           = intent_json.get("category", "")
    requirements       = intent_json.get("requirements", [])
    metrics_filters    = intent_json.get("metrics_filters", [])
    used_orchestrators = intent_json.get("used_orchestrators", [])

    if isinstance(layers, str):
        layers = [layers]
    if isinstance(used_orchestrators, str):
        used_orchestrators = [used_orchestrators]

    # ── Extraire les relations depuis db_schema ───────────────────────
    relations = _extract_relations(db_schema)

    try:
        query = _build_minimal_cypher(
            layers=layers,
            category=category,
            requirements=requirements,
            metrics_filters=metrics_filters,
            used_orchestrators=used_orchestrators,
            recommendation_policy=recommendation_policy,
            relations=relations,
        )
        print(f"\n[DEBUG cypher]:\n{query}")

        return {
            "minimal_cypher_query": query,
            "status":               "running",
        }

    except Exception as e:
        return {
            "errors": state.get("errors", []) + [f"cypher_query_generation_node: {e}"],
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


def _build_minimal_cypher(
    layers: list,
    category: str,
    requirements: list,
    metrics_filters: list,
    used_orchestrators: list,
    recommendation_policy: str,
    relations: dict,
) -> str:

    covers       = relations.get("covers", "COVERS")
    has_category = relations.get("has_category", "HAS_CATEGORY")
    supports     = relations.get("supports", "SUPPORTS")
    has_metrics  = relations.get("has_metrics", "HAS_METRICS")
    based_on     = relations.get("based_on", "BASED_ON")

    conditions    = []
    match_clauses = ["MATCH (o:Orchestrator)"]

    # ── Layers ───────────────────────────────────────────────────────
    if recommendation_policy == "composition_allowed" and layers:
        # Mode composition : au moins un layer suffit
        match_clauses.append(f"MATCH (o)-[:{covers}]->(l:Layer)")
        layers_list = str([layer.lower() for layer in layers])
        conditions.append(f"toLower(l.name) IN {layers_list}")
    else:
        # Mode normal : tous les layers requis simultanément
        for i, layer in enumerate(layers):
            alias = f"l{i}"
            match_clauses.append(f"MATCH (o)-[:{covers}]->({alias}:Layer)")
            conditions.append(f"toLower({alias}.name) = toLower('{layer}')")

    # ── Category ─────────────────────────────────────────────────────
    if category:
        match_clauses.append(f"MATCH (o)-[:{has_category}]->(cat:Category)")
        if recommendation_policy == "composition_allowed":
            conditions.append(
                f"(toLower(cat.name) = toLower('{category}') "
                f"OR toLower(cat.name) = toLower('Flow Orchestration'))"
            )
        else:
            conditions.append(f"toLower(cat.name) = toLower('{category}')")

    # ── Requirements (SUPPORTS) ───────────────────────────────────────
    if recommendation_policy == "composition_allowed" and requirements:
        # Mode composition : au moins un requirement suffit (OR)
        match_clauses.append(f"MATCH (o)-[:{supports}]->(cr:Criterion)")
        req_list = str([req.lower() for req in requirements])
        conditions.append(f"toLower(cr.name) IN {req_list}")
    else:
        # Mode normal : tous les requirements requis simultanément (AND)
        for i, req in enumerate(requirements):
            alias = f"cr{i}"
            match_clauses.append(f"MATCH (o)-[:{supports}]->({alias}:Criterion)")
            conditions.append(f"toLower({alias}.name) = toLower('{req}')")

    # ── Metrics filters (HAS_METRICS) ────────────────────────────────
    for i, mf in enumerate(metrics_filters):
        criterion_name = mf.get("criterion_name", "")
        operator       = mf.get("operator", "")
        alias_node     = f"mc{i}"
        alias_rel      = f"rm{i}"

        match_clauses.append(
            f"MATCH (o)-[{alias_rel}:{has_metrics}]->({alias_node}:Criterion)"
        )
        conditions.append(
            f"toLower({alias_node}.name) = toLower('{criterion_name}')"
        )

        if operator == ">=":
            value = mf.get("value")
            conditions.append(f"toInteger({alias_rel}.value) >= {value}")

        elif operator == "<=":
            value = mf.get("value")
            conditions.append(f"toInteger({alias_rel}.value) <= {value}")

        elif operator == "==":
            value = mf.get("value")
            conditions.append(
                f"toLower(toString({alias_rel}.value)) = toLower('{value}')"
            )

        elif operator == "contains_any":
            values = mf.get("values", [])
            or_conditions = " OR ".join([
                f"toLower(toString({alias_rel}.value)) CONTAINS toLower('{v}')"
                for v in values
            ])
            conditions.append(f"({or_conditions})")

    # ── Context uses ─────────────────────────────────────────────────
    if used_orchestrators:
        match_clauses.append(f"OPTIONAL MATCH (o)-[:{based_on}]->(base:Orchestrator)")

    # ── Assemble ─────────────────────────────────────────────────────
    query = "\n".join(match_clauses)
    if conditions:
        query += "\nWHERE " + "\n  AND ".join(conditions)

    if used_orchestrators:
        based_on_list = "', '".join(used_orchestrators)
        query += f"\nORDER BY CASE WHEN base.name IN ['{based_on_list}'] THEN 0 ELSE 1 END"

    query += "\nRETURN DISTINCT o"

    return query