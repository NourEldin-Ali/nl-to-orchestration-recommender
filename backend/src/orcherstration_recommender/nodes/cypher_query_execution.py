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
            minimal_result   = session.run(minimal_cypher_query)
            minimal_subgraph = [dict(record["o"]) for record in minimal_result]

            # ── Step 2 : If empty → return
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

            enriched_result   = session.run(enriched_cypher_query)
            enriched_subgraph = _parse_enriched_result(
                result=enriched_result,
                db_schema=db_schema,
            )

            return {
                "minimal_subgraph":      minimal_subgraph,
                "enriched_cypher_query": enriched_cypher_query,
                "enriched_subgraph":     enriched_subgraph,
                "status":                "running",
            }

    except Exception as e:
        return {
            "errors": state.get("errors", []) + [f"cypher_query_execution_node: {e}"],
            "status": "failed",
        }

    finally:
        driver.close()


def _build_enriched_cypher(minimal_cypher_query: str, db_schema: list) -> str:
    """
    Construit la requête enrichie dynamiquement depuis db_schema.
    Récupère toutes les relations sortantes depuis Orchestrator.
    """
    # Extraire toutes les relations depuis Orchestrator
    orchestrator_relations = [
        entry for entry in db_schema
        if entry.get("from") == "Orchestrator"
    ]

    base = minimal_cypher_query.rsplit("RETURN o", 1)[0]

    optional_matches = []
    return_clauses   = ["o"]

    for entry in orchestrator_relations:
        rel   = entry.get("relation", "")
        to    = entry.get("to", "")
        alias = to.lower() + "s"
        optional_matches.append(f"OPTIONAL MATCH (o)-[:{rel}]->(_{alias}:{to})")
        return_clauses.append(f"collect(DISTINCT _{alias}) AS {alias}")

    enriched = base + "\n"
    enriched += "\n".join(optional_matches)
    enriched += "\nRETURN " + ",\n       ".join(return_clauses)

    return enriched


def _parse_enriched_result(result, db_schema: list) -> list:
    """
    Parse le résultat enrichi dynamiquement depuis db_schema.
    """
    orchestrator_relations = [
        entry for entry in db_schema
        if entry.get("from") == "Orchestrator"
    ]

    enriched_subgraph = []

    for record in result:
        orchestrator = dict(record["o"])

        for entry in orchestrator_relations:
            to    = entry.get("to", "")
            alias = to.lower() + "s"
            try:
                orchestrator[alias] = [dict(n) for n in record[alias]]
            except KeyError:
                orchestrator[alias] = []

        enriched_subgraph.append(orchestrator)

    return enriched_subgraph