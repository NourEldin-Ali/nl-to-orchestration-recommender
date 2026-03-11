import uuid
from src.orcherstration_recommender.state import State
from src.config.neo4j_config import Neo4jConnector


def intent_graph_generation_node(state: State) -> State:
    """
    Component 1 — SLM | Intent Graph Generation
    Structured code only — no LLM required.
    Reads  : intent_json
    Writes : intent_graph_created, recommendation_policy (default: single_only), attempt_try (default: 1)
    """
    intent_json = state.get("intent_json", {})
    intent_id   = str(uuid.uuid4())

    layers             = intent_json.get("layers", [])
    category           = intent_json.get("category", "")
    requirements       = intent_json.get("requirements", [])
    used_orchestrators = intent_json.get("used_orchestrators", [])

    # Normalise to list
    if isinstance(layers, str):
        layers = [layers]
    if isinstance(used_orchestrators, str):
        used_orchestrators = [used_orchestrators]

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
                session.run("""
                    MATCH (i:Intent {id: $id})
                    MERGE (l:Layer {name: $layer})
                    CREATE (i)-[:COVERS]->(l)
                """, id=intent_id, layer=layer)

            # 3. (I)-[:HAS_CATEGORY]->(Category)
            if category:
                session.run("""
                    MATCH (i:Intent {id: $id})
                    MERGE (c:Category {name: $category})
                    CREATE (i)-[:HAS_CATEGORY]->(c)
                """, id=intent_id, category=category)

            # 4. (I)-[:REQUIRES]->(Criterion)
            for requirement in requirements:
                session.run("""
                    MATCH (i:Intent {id: $id})
                    MERGE (cr:Criterion {name: $requirement})
                    CREATE (i)-[:REQUIRES]->(cr)
                """, id=intent_id, requirement=requirement)

            # 5. (I)-[:CONTEXT_USES]->(Orchestrator)
            for orchestrator in used_orchestrators:
                session.run("""
                    MATCH (i:Intent {id: $id})
                    MATCH (o:Orchestrator {name: $orchestrator})
                    CREATE (i)-[:CONTEXT_USES]->(o)
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