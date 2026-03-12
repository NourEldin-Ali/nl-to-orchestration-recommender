from src.orcherstration_recommender.state import State
from src.orcherstration_recommender.prompts.prompts_list import INTENT_DETECTION_PROMPT
from src.config.neo4j_config import Neo4jConnector
from langchain_core.messages import SystemMessage


def intent_graph_update_node(state: State, llm) -> State:
    """
    Component 1 — SLM | Intent Graph Update
    Triggered after user responds to composition explanation.
    Reads  : messages, intent_id, attempt_try, db_schema, db_vocabulary
    Writes : recommendation_policy, attempt_try (incremented)
    """
    intent_id     = state.get("intent_id", "")
    attempt_try   = state.get("attempt_try", 1)
    messages      = state.get("messages", [])
    db_schema     = state.get("db_schema", [])
    db_vocabulary = state.get("db_vocabulary", {})

    # ── Extraire les relations depuis db_schema ───────────────────────
    has_category = _extract_has_category_relation(db_schema)

    # ── Récupérer la valeur exacte de flow orchestration depuis db_vocabulary
    categories    = db_vocabulary.get("categorys", [])
    flow_category = next(
        (c for c in categories if "flow" in c.lower()),
        None
    )

    # ── Extract last user message ─────────────────────────────────────
    user_response = next(
        (m.content.strip() for m in reversed(messages) if m.type == "human"), ""
    )

    # ── 1. LLM classifies user response ──────────────────────────────
    response = llm.invoke([
        SystemMessage(content=INTENT_DETECTION_PROMPT.format(user_response=user_response))
    ])
    recommendation_policy = response.content.strip().lower()

    if recommendation_policy not in {"composition_allowed", "composition_not_allowed"}:
        recommendation_policy = "composition_not_allowed"

    # ── 2. Update Neo4j ───────────────────────────────────────────────
    driver = Neo4jConnector().get_driver()
    try:
        with driver.session() as session:
            session.run("""
                MATCH (i:Intent {id: $id})
                SET i.recommendation_policy = $policy,
                    i.attempt_try           = $attempt_try
            """, id=intent_id, policy=recommendation_policy, attempt_try=attempt_try + 1)

            if recommendation_policy == "composition_allowed" and flow_category:
                session.run(f"""
                    MATCH (i:Intent {{id: $id}})
                    MATCH (c:Category {{name: $category}})
                    MERGE (i)-[:{has_category}]->(c)
                """, id=intent_id, category=flow_category)

    finally:
        driver.close()

    return {
        "recommendation_policy": recommendation_policy,
        "attempt_try":           attempt_try + 1,
        "status":                "running",
    }


def _extract_has_category_relation(db_schema: list) -> str:
    """
    Extrait la relation HAS_CATEGORY depuis db_schema.
    """
    for entry in db_schema:
        if entry.get("from") == "Orchestrator" and entry.get("to") == "Category":
            return entry.get("relation", "HAS_CATEGORY")
    return "HAS_CATEGORY"