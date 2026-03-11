from src.orcherstration_recommender.state import State


def cypher_query_generation_node(state: State) -> State:
    """
    Component 2 — Reasoner | Cypher Query Generation
    Structured code only — no LLM required.
    Reads  : intent_json, recommendation_policy, attempt_try
    Writes : minimal_cypher_query
    """
    intent_json           = state.get("intent_json", {})
    recommendation_policy = state.get("recommendation_policy", "single_only")

    layers             = intent_json.get("layers", [])
    category           = intent_json.get("category", "")
    requirements       = intent_json.get("requirements", [])
    used_orchestrators = intent_json.get("used_orchestrators", [])

    if isinstance(layers, str):
        layers = [layers]
    if isinstance(used_orchestrators, str):
        used_orchestrators = [used_orchestrators]

    try:
        query = _build_minimal_cypher(
            layers=layers,
            category=category,
            requirements=requirements,
            used_orchestrators=used_orchestrators,
            recommendation_policy=recommendation_policy,
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


def _build_minimal_cypher(
    layers: list,
    category: str,
    requirements: list,
    used_orchestrators: list,
    recommendation_policy: str,
) -> str:
    conditions    = []
    match_clauses = ["MATCH (o:Orchestrator)"]

    # ── Layers ───────────────────────────────────────────────────────
    for i, layer in enumerate(layers):
        alias = f"l{i}"
        match_clauses.append(f"MATCH (o)-[:COVERS]->({alias}:Layer)")
        conditions.append(f"toLower({alias}.name) = toLower('{layer}')")

    # ── Category ─────────────────────────────────────────────────────
    if category:
        match_clauses.append("MATCH (o)-[:HAS_CATEGORY]->(cat:Category)")
        if recommendation_policy == "composition_allowed":
            conditions.append(
                f"(toLower(cat.name) = toLower('{category}') "
                f"OR toLower(cat.name) = toLower('Flow Orchestration'))"
            )
        else:
            conditions.append(f"toLower(cat.name) = toLower('{category}')")

    # ── Requirements ─────────────────────────────────────────────────
    for i, req in enumerate(requirements):
        alias = f"cr{i}"
        match_clauses.append(f"MATCH (o)-[:SUPPORTS]->({alias}:Criterion)")
        conditions.append(f"toLower({alias}.name) = toLower('{req}')")

    # ── Context uses (OPTIONAL — used for ranking, not filtering) ────
    if used_orchestrators:
        match_clauses.append("OPTIONAL MATCH (o)-[:BASED_ON]->(base:Orchestrator)")

    # ── Assemble ─────────────────────────────────────────────────────
    query = "\n".join(match_clauses)
    if conditions:
        query += "\nWHERE " + "\n  AND ".join(conditions)

    # ── Order by context_uses match (prioritize tools based on used ones)
    if used_orchestrators:
        based_on_list = "', '".join(used_orchestrators)
        query += f"\nORDER BY CASE WHEN base.name IN ['{based_on_list}'] THEN 0 ELSE 1 END"

    query += "\nRETURN o"

    return query