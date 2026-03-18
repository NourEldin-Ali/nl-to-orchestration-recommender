from src.orcherstration_recommender.state import State
from src.config.neo4j_config import Neo4jConnector


EXCLUDED_LABELS = {"Intent"}


def db_schema_discovery_node(state: State) -> State:
    """
    DB Discovery — Node 1 | Schema Discovery
    Algo pur, 0 LLM.
    Reads  : nothing
    Writes : db_schema
    """
    driver = Neo4jConnector().get_driver()

    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (a)-[r]->(b)
                RETURN DISTINCT labels(a)[0] AS from, type(r) AS relation, labels(b)[0] AS to, keys(r) AS relation_properties
            """)

            db_schema_raw = [
                {
                    "from":                record["from"],
                    "relation":            record["relation"],
                    "to":                  record["to"],
                    "relation_properties": list(record["relation_properties"]),
                }
                for record in result
                if record["from"] not in EXCLUDED_LABELS
                and record["to"] not in EXCLUDED_LABELS
            ]

        # ── Dédupliquer par (from, relation, to) ─────────────────────
        seen      = set()
        db_schema = []
        for entry in db_schema_raw:
            key = (entry["from"], entry["relation"], entry["to"])
            if key not in seen:
                seen.add(key)
                db_schema.append(entry)

        print(f"\n[DEBUG db_schema]:")
        for entry in db_schema:
            props = entry.get("relation_properties", [])
            print(f"  ({entry['from']})-[:{entry['relation']}]->({entry['to']}) props={props}")

        return {
            "db_schema": db_schema,
            "status":    "running",
        }

    except Exception as e:
        print(f"\n[DEBUG db_schema_discovery ERROR]: {e}")
        return {
            "errors": state.get("errors", []) + [f"db_schema_discovery_node: {e}"],
            "status": "failed",
        }

    finally:
        driver.close()