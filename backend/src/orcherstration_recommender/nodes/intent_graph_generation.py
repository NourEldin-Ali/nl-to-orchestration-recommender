import uuid
from src.orcherstration_recommender.state import State
from src.config.neo4j_config import Neo4jConnector


def intent_graph_generation_node(state: State) -> State:
    """
    Component 1 — SLM | Intent Graph Generation
    Structured code only — no LLM required.
    Reads  : intent_json, db_schema
    Writes : intent_graph_created, recommendation_policy, attempt_try
    """
    intent_json = state.get("intent_json", {})
    db_schema   = state.get("db_schema", [])
    intent_id   = str(uuid.uuid4())

    layers             = intent_json.get("layers", [])
    category           = intent_json.get("category", "")
    requirements       = intent_json.get("requirements", [])
    used_orchestrators = intent_json.get("used_orchestrators", [])

    if isinstance(layers, str):
        layers = [layers]
    if isinstance(used_orchestrators, str):
        used_orchestrators = [used_orchestrators]

    # ── Extraire les relations depuis db_schema ───────────────────────
    relations    = _extract_relations(db_schema)
    covers       = relations.get("covers", "COVERS")
    has_category = relations.get("has_category", "HAS_CATEGORY")
    based_on     = relations.get("based_on", "BASED_ON")

    driver = Neo4jConnector().get_driver()

    try:
        with driver.session() as session:

            # 1. Create Intent node
            session.run("""
                CREATE (i:Intent {
                    id:                    $id,
                    user_query:            $user_query,
                    recommendation_policy: 'single_only',
                    attempt_try:           1,
                    coverage:              null,
                    final_recommendation:  null
                })
            """, id=intent_id, user_query=state.get("user_query", ""))

            # 2. (I)-[:COVERS]->(Layer)
            for layer in layers:
                session.run(f"""
                    MATCH (i:Intent {{id: $id}})
                    MATCH (l:Layer {{name: $layer}})
                    CREATE (i)-[:{covers}]->(l)
                """, id=intent_id, layer=layer)

            # 3. (I)-[:HAS_CATEGORY]->(Category)
            if category:
                session.run(f"""
                    MATCH (i:Intent {{id: $id}})
                    MATCH (c:Category {{name: $category}})
                    CREATE (i)-[:{has_category}]->(c)
                """, id=intent_id, category=category)

            # 4. (I)-[:REQUIRES]->(Criterion)
            for requirement in requirements:
                session.run(f"""
                    MATCH (i:Intent {{id: $id}})
                    MATCH (cr:Criterion {{name: $requirement}})
                    CREATE (i)-[:REQUIRES]->(cr)
                """, id=intent_id, requirement=requirement)

            # 5. (I)-[:CONTEXT_USES]->(Orchestrator)
            for orchestrator in used_orchestrators:
                session.run(f"""
                    MATCH (i:Intent {{id: $id}})
                    MATCH (o:Orchestrator {{name: $orchestrator}})
                    CREATE (i)-[:{based_on}]->(o)
                """, id=intent_id, orchestrator=orchestrator)

        return {
            "intent_id":             intent_id,
            "intent_graph_created":  True,
            "recommendation_policy": "single_only",
            "attempt_try":           1,
            "status":                "running",
        }

    except Exception as e:
        return {
            "intent_graph_created": False,
            "errors": state.get("errors", []) + [f"intent_graph_generation_node: {e}"],
            "status": "failed",
        }

    finally:
        driver.close()


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
            elif to == "Orchestrator":
                relations["based_on"] = rel
    return relations