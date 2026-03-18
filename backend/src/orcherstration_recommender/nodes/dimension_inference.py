import json
import datetime
from src.orcherstration_recommender.state import State
from src.orcherstration_recommender.prompts.prompts_list import DIMENSION_INFERENCE_PROMPT
from src.config.neo4j_config import Neo4jConnector
from langchain_core.messages import SystemMessage


def dimension_inference_node(state: State, llm) -> State:
    """
    Intent Extraction — Node 3.5 | Dimension Inference
    Reads  : user_query
    Writes : detected_metrics_filters
    """
    user_query   = state.get("user_query", "")
    current_year = datetime.datetime.now().year

    # ── Récupérer les critères HAS_METRICS avec leurs valeurs distinctes ──
    metrics_vocabulary = _build_metrics_vocabulary()

    print(f"\n[DEBUG dimension_inference]:")
    print(f"  current_year       : {current_year}")
    print(f"  metrics_vocabulary : {metrics_vocabulary}")

    messages = [
        SystemMessage(content=DIMENSION_INFERENCE_PROMPT.format(
            user_query=user_query,
            metrics_vocabulary=json.dumps(metrics_vocabulary, indent=2),
            current_year=current_year,
        ))
    ]

    try:
        response = llm.invoke(messages)
        raw = response.content.strip()

        if raw.startswith("```json"):
            raw = raw[7:]
        elif raw.startswith("```"):
            raw = raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()

        result = json.loads(raw)
        detected_metrics_filters = result.get("metrics_filters", [])

        print(f"  detected_metrics_filters : {detected_metrics_filters}")

        return {
            "detected_metrics_filters": detected_metrics_filters,
            "status":                   "running",
        }

    except Exception as e:
        print(f"\n[DEBUG dimension_inference ERROR]: {e}")
        return {
            "errors": state.get("errors", []) + [f"dimension_inference_node: {e}"],
            "status": "failed",
        }


def _build_metrics_vocabulary() -> dict:
    """
    Récupère dynamiquement depuis Neo4j les critères HAS_METRICS
    et leurs valeurs distinctes.
    """
    driver = Neo4jConnector().get_driver()

    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (o:Orchestrator)-[r:HAS_METRICS]->(c:Criterion)
                WHERE r.value IS NOT NULL
                RETURN DISTINCT c.name AS criterion, collect(DISTINCT toString(r.value)) AS values
                ORDER BY c.name
            """)

            metrics_vocabulary = {}
            for record in result:
                criterion = record["criterion"]
                values    = record["values"]
                metrics_vocabulary[criterion] = values

        return metrics_vocabulary

    finally:
        driver.close()