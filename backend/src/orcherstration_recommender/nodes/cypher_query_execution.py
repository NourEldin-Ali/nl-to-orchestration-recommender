from src.orcherstration_recommender.state import State
from src.config.neo4j_config import Neo4jConnector


def cypher_query_execution_node(state: State) -> State:
    """
    Component 2 — Reasoner | Cypher Query Execution
    Calls Neo4j — no LLM required.
    Reads  : minimal_cypher_query, enriched_cypher_query, db_schema
    Writes : minimal_subgraph, enriched_subgraph
    """
    minimal_cypher_query  = state.get("minimal_cypher_query", "")
    enriched_cypher_query = state.get("enriched_cypher_query", "")
    db_schema             = state.get("db_schema", [])

    driver = Neo4jConnector().get_driver()

    try:
        with driver.session() as session:

            # ── Step 1 : Execute minimal query ───────────────────────
            minimal_result = session.run(minimal_cypher_query)
            records        = list(minimal_result)

            print(f"\n[DEBUG cypher_execution]:")
            print(f"  records count : {len(records)}")
            if records:
                print(f"  first record  : {records[0]}")
                print(f"  type          : {type(records[0]['o'])}")

            minimal_subgraph = [dict(record["o"].items()) for record in records]

            print(f"  minimal_subgraph length : {len(minimal_subgraph)}")

            # ── Step 2 : If empty → return ────────────────────────────
            if not minimal_subgraph:
                return {
                    "minimal_subgraph":  [],
                    "enriched_subgraph": [],
                    "status":            "running",
                }

            # ── Step 3 : Build and execute enriched query ─────────────
            if not enriched_cypher_query:
                enriched_cypher_query = _build_enriched_cypher(
                    minimal_cypher_query=minimal_cypher_query,
                    db_schema=db_schema,
                )

            print(f"\n[DEBUG enriched_cypher]:\n{enriched_cypher_query}")

            enriched_result   = session.run(enriched_cypher_query)
            enriched_subgraph = _parse_enriched_result(
                result=enriched_result,
                db_schema=db_schema,
            )

            print(f"\n[DEBUG enriched_subgraph length]: {len(enriched_subgraph)}")
            if enriched_subgraph:
                print(f"  first enriched : {enriched_subgraph[0]}")

            return {
                "minimal_subgraph":      minimal_subgraph,
                "enriched_cypher_query": enriched_cypher_query,
                "enriched_subgraph":     enriched_subgraph,
                "status":                "running",
            }

    except Exception as e:
        print(f"\n[DEBUG cypher_execution ERROR]: {e}")
        return {
            "errors": state.get("errors", []) + [f"cypher_query_execution_node: {e}"],
            "status": "failed",
        }

    finally:
        driver.close()


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


def _build_enriched_cypher(minimal_cypher_query: str, db_schema: list) -> str:
    """
    Construit la requête enrichie dynamiquement depuis db_schema.
    Récupère toutes les relations sortantes depuis Orchestrator.
    Utilise le nom de la relation comme alias pour éviter les collisions.
    Si la relation porte des propriétés, les inclut dans le collect.
    """
    orchestrator_relations = [
        entry for entry in db_schema
        if entry.get("from") == "Orchestrator"
    ]

    base = minimal_cypher_query.rsplit("RETURN DISTINCT o", 1)[0]

    optional_matches = []
    return_clauses   = ["o"]

    for entry in orchestrator_relations:
        rel            = entry.get("relation", "")
        to             = entry.get("to", "")
        alias          = rel.lower()
        rel_properties = entry.get("relation_properties", [])

        if rel_properties:
            props = ", ".join([f"{p}: r_{alias}.{p}" for p in rel_properties])
            optional_matches.append(
                f"OPTIONAL MATCH (o)-[r_{alias}:{rel}]->(_{alias}:{to})"
            )
            return_clauses.append(
                f"collect(DISTINCT {{name: _{alias}.name, id: _{alias}.id, {props}}}) AS {alias}"
            )
        else:
            optional_matches.append(
                f"OPTIONAL MATCH (o)-[:{rel}]->(_{alias}:{to})"
            )
            return_clauses.append(
                f"collect(DISTINCT _{alias}) AS {alias}"
            )

    enriched = base + "\n"
    enriched += "\n".join(optional_matches)
    enriched += "\nRETURN " + ",\n       ".join(return_clauses)

    return enriched


def _parse_enriched_result(result, db_schema: list) -> list:
    """
    Parse le résultat enrichi dynamiquement depuis db_schema.
    Utilise le nom de la relation comme clé.
    """
    orchestrator_relations = [
        entry for entry in db_schema
        if entry.get("from") == "Orchestrator"
    ]

    enriched_subgraph = []

    for record in result:
        orchestrator = dict(record["o"].items())

        for entry in orchestrator_relations:
            rel            = entry.get("relation", "")
            alias          = rel.lower()
            rel_properties = entry.get("relation_properties", [])

            try:
                if rel_properties:
                    orchestrator[alias] = [dict(n) for n in record[alias]]
                else:
                    orchestrator[alias] = [dict(n.items()) for n in record[alias]]
            except KeyError:
                orchestrator[alias] = []

        enriched_subgraph.append(orchestrator)

    return enriched_subgraph