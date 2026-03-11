from src.orcherstration_recommender.state import State
from src.orcherstration_recommender.prompts.prompts_list import INTENT_DETECTION_PROMPT
from src.config.neo4j_config import Neo4jConnector
from langchain_core.messages import SystemMessage


def intent_graph_update_node(state: State, llm) -> State:
    """
    Component 1 — SLM | Intent Graph Update
    Triggered after user responds to composition explanation.
    Reads  : messages (last user message), intent_id, attempt_try
    Writes : recommendation_policy (composition_allowed | composition_not_allowed),
             attempt_try (incremented)
    """
    intent_id   = state.get("intent_id", "")
    attempt_try = state.get("attempt_try", 1)
    messages    = state.get("messages", [])

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
    with driver.session() as session:
        session.run("""
            MATCH (i:Intent {id: $id})
            SET i.recommendation_policy = $policy,
                i.attempt_try           = $attempt_try
        """, id=intent_id, policy=recommendation_policy, attempt_try=attempt_try + 1)

        if recommendation_policy == "composition_allowed":
            session.run("""
                MATCH (i:Intent {id: $id})
                MERGE (c:Category {name: 'flow_orchestration'})
                MERGE (i)-[:HAS_CATEGORY]->(c)
            """, id=intent_id)
    driver.close()

    return {
        "recommendation_policy": recommendation_policy,
        "attempt_try":           attempt_try + 1,
        "status":                "running",
    }