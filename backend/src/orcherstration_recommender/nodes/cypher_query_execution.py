import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../../.."))

from orcherstration_recommender.state import State
from config.neo4j_config import Neo4jConnector


def cypher_query_execution_node(state: State) -> State:
    """
    Component 2 — Reasoner | Cypher Query Execution
    Calls Neo4j — no LLM required.
    Reads  : minimal_cypher_query, enriched_cypher_query (if exists)
    Writes : minimal_subgraph, enriched_subgraph (if minimal_subgraph not empty)
    """
    minimal_cypher_query  = state.get("minimal_cypher_query", "")
    enriched_cypher_query = state.get("enriched_cypher_query", "")

    driver = Neo4jConnector().get_driver()

    try:
        with driver.session() as session:

            # ── Step 1 : Execute minimal query ───────────────────────
            minimal_result = session.run(minimal_cypher_query)
            minimal_subgraph = [dict(record["o"]) for record in minimal_result]

            # ── Step 2 : If empty → return, composition handler will be triggered
            if not minimal_subgraph:
                return {
                    "minimal_subgraph": [],
                    "enriched_subgraph": [],
                    "status": "running",
                }

            # ── Step 3 : Build and execute enriched query ─────────────
            if not enriched_cypher_query:
                enriched_cypher_query = _build_enriched_cypher(minimal_cypher_query)

            enriched_result  = session.run(enriched_cypher_query)
            enriched_subgraph = _parse_enriched_result(enriched_result)

            return {
                "minimal_subgraph":     minimal_subgraph,
                "enriched_cypher_query": enriched_cypher_query,
                "enriched_subgraph":    enriched_subgraph,
                "status":               "running",
            }

    except Exception as e:
        return {
            "errors": state.get("errors", []) + [f"cypher_query_execution_node: {e}"],
            "status": "failed",
        }

    finally:
        driver.close()


def _build_enriched_cypher(minimal_query: str) -> str:
    """
    Builds the enriched Cypher query from the minimal one.
    Extends the RETURN clause to include all relations:
    criteria, dimensions, layers, category.
    """
    # Remove the last RETURN o and replace with enriched RETURN
    base = minimal_query.rsplit("RETURN o", 1)[0]

    enriched = base + """
OPTIONAL MATCH (o)-[:SUPPORTS]->(cr:Criterion)
OPTIONAL MATCH (o)-[:HAS_METRICS]->(cm:Criterion)
OPTIONAL MATCH (o)-[:COVERS]->(l:Layer)
OPTIONAL MATCH (o)-[:HAS_CATEGORY]->(cat:Category)
OPTIONAL MATCH (cr)<-[:HAS_CRITERION]-(d:Dimension)
OPTIONAL MATCH (o)-[:BASED_ON]->(base:Orchestrator)
RETURN o,
       collect(DISTINCT cr)   AS supported_criteria,
       collect(DISTINCT cm)   AS metrics_criteria,
       collect(DISTINCT l)    AS layers,
       collect(DISTINCT cat)  AS categories,
       collect(DISTINCT d)    AS dimensions,
       collect(DISTINCT base) AS based_on
"""
    return enriched


def _parse_enriched_result(result) -> list:
    """
    Parses the enriched query result into a list of dicts.
    Each dict represents one orchestrator with all its relations.
    """
    enriched_subgraph = []

    for record in result:
        orchestrator = dict(record["o"])
        orchestrator["supported_criteria"] = [dict(c) for c in record["supported_criteria"]]
        orchestrator["metrics_criteria"]   = [dict(c) for c in record["metrics_criteria"]]
        orchestrator["layers"]             = [dict(l) for l in record["layers"]]
        orchestrator["categories"]         = [dict(c) for c in record["categories"]]
        orchestrator["dimensions"]         = [dict(d) for d in record["dimensions"]]
        orchestrator["based_on"]           = [dict(b) for b in record["based_on"]]
        enriched_subgraph.append(orchestrator)

    return enriched_subgraph