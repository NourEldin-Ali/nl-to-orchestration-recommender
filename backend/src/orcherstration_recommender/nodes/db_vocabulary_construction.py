from src.orcherstration_recommender.state import State
from src.config.neo4j_config import Neo4jConnector


EXCLUDED_LABELS = {"Intent"}


def db_vocabulary_node(state: State) -> State:
    """
    DB Discovery — Node 2 | Vocabulary Extraction
    Algo pur, 0 LLM.
    Reads  : db_schema
    Writes : db_vocabulary {layers, categories, criteria, orchestrators}
    """
    db_schema = state.get("db_schema", [])

    # Extraire les labels distincts en excluant les labels non pertinents
    labels = set()
    for entry in db_schema:
        if entry.get("from") not in EXCLUDED_LABELS:
            labels.add(entry.get("from", ""))
        if entry.get("to") not in EXCLUDED_LABELS:
            labels.add(entry.get("to", ""))

    driver = Neo4jConnector().get_driver()

    try:
        with driver.session() as session:

            db_vocabulary = {}

            for label in labels:
                if not label:
                    continue

                result = session.run(f"""
                    MATCH (n:{label})
                    WHERE n.name IS NOT NULL
                    RETURN DISTINCT n.name AS name
                    ORDER BY n.name
                """)

                values = [record["name"] for record in result]

                if values:
                    db_vocabulary[label.lower()] = values

        print(f"\n[DEBUG db_vocabulary]:")
        for key, values in db_vocabulary.items():
            print(f"  {key}: {values}")

        return {
            "db_vocabulary": db_vocabulary,
            "status":        "running",
        }

    except Exception as e:
        print(f"\n[DEBUG db_vocabulary ERROR]: {e}")
        return {
            "errors": state.get("errors", []) + [f"db_vocabulary_node: {e}"],
            "status": "failed",
        }

    finally:
        driver.close()