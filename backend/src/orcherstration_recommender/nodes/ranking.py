from src.orcherstration_recommender.state import State
from src.config.neo4j_config import Neo4jConnector


def candidates_ranking_node(state: State) -> State:
    """
    Component 2 — Reasoner | Candidates Ranking
    Structured code only — no LLM required.
    Reads  : enriched_subgraph, final_recommendation, recommendation_policy, intent_json
    Writes : enriched_subgraph (filtered and ranked)
    """
    enriched_subgraph     = state.get("enriched_subgraph", [])
    final_recommendation  = state.get("final_recommendation", "None")
    recommendation_policy = state.get("recommendation_policy", "single_only")
    intent_json           = state.get("intent_json", {})

    # ── Extract required layers from intent ──────────────────────────
    required_layers = intent_json.get("layers", [])
    if isinstance(required_layers, str):
        required_layers = [required_layers]
    required_layers_lower = [l.lower() for l in required_layers]

    # ── Determine how many candidates to keep ────────────────────────
    if final_recommendation == "SingleCandidate":
        limit = 1
    elif final_recommendation == "MultipleCandidates":
        if recommendation_policy == "single_only":
            limit = 2  # top 2 for user to choose
        else:
            limit = 2
    elif final_recommendation == "CompositionOfTools":
        limit = len(enriched_subgraph)  # keep all for composition
    else:
        print(f"\n[DEBUG candidates_ranking]: final_recommendation='{final_recommendation}', no ranking applied")
        return {
            "enriched_subgraph": enriched_subgraph,
            "status":            "running",
        }

    if len(enriched_subgraph) <= limit:
        print(f"\n[DEBUG candidates_ranking]: already {len(enriched_subgraph)} candidates, no ranking needed")
        return {
            "enriched_subgraph": enriched_subgraph,
            "status":            "running",
        }

    # ── Filter candidates that cover ALL required layers ─────────────
    # This ensures that e.g. Kubernetes (Cloud only) is not ranked above
    # KubeEdge (Cloud + Edge) when the intent requires both layers.
    if len(required_layers_lower) > 1:
        filtered_subgraph = []
        for o in enriched_subgraph:
            covers = [c.get("name", "").lower() for c in o.get("covers", [])]
            if all(layer in covers for layer in required_layers_lower):
                filtered_subgraph.append(o)

        # Only apply filter if it leaves at least `limit` candidates
        # Otherwise fall back to the full subgraph
        if len(filtered_subgraph) >= limit:
            enriched_subgraph = filtered_subgraph
            print(f"\n[DEBUG candidates_ranking]: filtered to {len(enriched_subgraph)} candidates covering all required layers")
        else:
            print(f"\n[DEBUG candidates_ranking]: layer filter too restrictive ({len(filtered_subgraph)} left), using full subgraph")

    # ── Extract orchestrator names ────────────────────────────────────
    names = [o.get("name", "") for o in enriched_subgraph if o.get("name")]

    print(f"\n[DEBUG candidates_ranking]:")
    print(f"  final_recommendation  : {final_recommendation}")
    print(f"  recommendation_policy : {recommendation_policy}")
    print(f"  required_layers       : {required_layers_lower}")
    print(f"  limit                 : {limit}")
    print(f"  candidates            : {names}")

    # ── Ranking query by stars + forks ────────────────────────────────
    ranking_query = f"""
        MATCH (o:Orchestrator)
        WHERE toLower(o.name) IN {str([n.lower() for n in names])}

        OPTIONAL MATCH (o)-[rs:HAS_METRICS]->(ms)
        WHERE ms.id = 'C.stars'

        OPTIONAL MATCH (o)-[rf:HAS_METRICS]->(mf)
        WHERE mf.id = 'C.forks'

        WITH o,
        CASE
            WHEN rs.value IS NULL THEN 0
            WHEN toLower(toString(rs.value)) = 'unavailable' THEN 0
            WHEN toLower(toString(rs.value)) CONTAINS 'k' THEN
                toFloat(replace(toLower(toString(rs.value)), 'k', '')) * 1000
            ELSE
                toFloat(rs.value)
        END AS stars,
        CASE
            WHEN rf.value IS NULL THEN 0
            WHEN toLower(toString(rf.value)) = 'unavailable' THEN 0
            WHEN toLower(toString(rf.value)) CONTAINS 'k' THEN
                toFloat(replace(toLower(toString(rf.value)), 'k', '')) * 1000
            ELSE
                toFloat(rf.value)
        END AS forks

        WITH o, stars, forks, stars + forks AS score
        ORDER BY score DESC
        RETURN o.name AS name, stars, forks, score
        LIMIT {limit}
    """

    print(f"\n[DEBUG ranking_query]:\n{ranking_query}")

    driver = Neo4jConnector().get_driver()

    try:
        with driver.session() as session:
            result  = session.run(ranking_query)
            records = list(result)

            print(f"\n[DEBUG ranking results]:")
            for r in records:
                print(f"  {r['name']} — stars: {r['stars']}, forks: {r['forks']}, score: {r['score']}")

            ranked_names = [r["name"] for r in records]

        # ── Filter enriched_subgraph to keep only ranked candidates ──
        ranked_subgraph = [
            o for o in enriched_subgraph
            if o.get("name") in ranked_names
        ]

        # ── Preserve ranking order ────────────────────────────────────
        ranked_subgraph.sort(key=lambda o: ranked_names.index(o.get("name")))

        print(f"\n[DEBUG ranked_subgraph]: {[o.get('name') for o in ranked_subgraph]}")

        return {
            "enriched_subgraph": ranked_subgraph,
            "status":            "running",
        }

    except Exception as e:
        print(f"\n[DEBUG candidates_ranking ERROR]: {e}")
        return {
            "errors": state.get("errors", []) + [f"candidates_ranking_node: {e}"],
            "status": "failed",
        }

    finally:
        driver.close()