from functools import partial
from time import perf_counter
from typing import Callable

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from src.config.llm_config import LLMConnector
from src.orcherstration_recommender.edge import (
    after_db_vocabulary,
    after_cypher_query_execution,
    after_intent_graph_update,
    after_start,
)
from src.orcherstration_recommender.execution_timing import add_execution_timing
from src.orcherstration_recommender.nodes.category_extraction import category_extraction_node
from src.orcherstration_recommender.nodes.composition_requirement_explanation import composition_requirement_explanation_node
from src.orcherstration_recommender.nodes.cypher_query_execution import cypher_query_execution_node
from src.orcherstration_recommender.nodes.cypher_query_generation import cypher_query_generation_node
from src.orcherstration_recommender.nodes.db_schema_discovery import db_schema_discovery_node
from src.orcherstration_recommender.nodes.db_vocabulary_construction import db_vocabulary_node
from src.orcherstration_recommender.nodes.dimension_inference import dimension_inference_node
from src.orcherstration_recommender.nodes.graph_to_natural_language import graph_to_natural_language_node
from src.orcherstration_recommender.nodes.intent_aligned_justification import intent_aligned_justification_node
from src.orcherstration_recommender.nodes.intent_coverage_verifier import intent_coverage_verifier_node
from src.orcherstration_recommender.nodes.intent_extraction import intent_combination_node
from src.orcherstration_recommender.nodes.intent_graph_generation import intent_graph_generation_node
from src.orcherstration_recommender.nodes.intent_graph_update import intent_graph_update_node
from src.orcherstration_recommender.nodes.layer_extraction import layer_extraction_node
from src.orcherstration_recommender.nodes.ranking import candidates_ranking_node
from src.orcherstration_recommender.nodes.recommandantion_baseline import recommandantion_baseline
from src.orcherstration_recommender.nodes.requirements_extraction import requirements_extraction_node
from src.orcherstration_recommender.nodes.used_orchestrators_extraction import used_orchestrators_extraction_node
from src.orcherstration_recommender.state import State
from src.orcherstration_recommender.token_usage import ensure_node_token_usage


def timed_node(node_name: str, node_fn: Callable[[State], dict]) -> Callable[[State], dict]:
    def _wrapped(state: State) -> dict:
        start = perf_counter()
        result = node_fn(state)
        elapsed_seconds = perf_counter() - start

        if not isinstance(result, dict):
            return result

        updated_result = dict(result)
        if "token_usage" not in updated_result:
            updated_result["token_usage"] = ensure_node_token_usage(state, node_name)
        updated_result["execution_timing"] = add_execution_timing(state, node_name, elapsed_seconds)
        return updated_result

    return _wrapped


def build_graph(
    one_step: bool = False,
    based_on_existing_orchestrator: bool = False,
    based_on_exiting_orchestrator: bool | None = None,
):
    if based_on_exiting_orchestrator is not None:
        based_on_existing_orchestrator = based_on_exiting_orchestrator

    llm = LLMConnector()()
    builder = StateGraph(State)

    # ── Nodes ──────────────────────────────────────────────────────────
    builder.add_node("db_schema_discovery",                 timed_node("db_schema_discovery", db_schema_discovery_node))
    builder.add_node("db_vocabulary",                       timed_node("db_vocabulary", db_vocabulary_node))
    builder.add_node("layer_extraction",                    timed_node("layer_extraction", partial(layer_extraction_node, llm=llm)))
    builder.add_node("category_extraction",                 timed_node("category_extraction", partial(category_extraction_node, llm=llm)))
    builder.add_node("requirements_extraction",             timed_node("requirements_extraction", partial(requirements_extraction_node, llm=llm)))
    builder.add_node("dimension_inference",                 timed_node("dimension_inference", partial(dimension_inference_node, llm=llm)))
    builder.add_node("used_orchestrators_extraction",       timed_node("used_orchestrators_extraction", partial(used_orchestrators_extraction_node, llm=llm)))
    builder.add_node("intent_combination",                  timed_node("intent_combination", intent_combination_node))
    builder.add_node("intent_graph_generation",             timed_node("intent_graph_generation", intent_graph_generation_node))
    builder.add_node("cypher_query_generation",             timed_node("cypher_query_generation", cypher_query_generation_node))
    builder.add_node("cypher_query_execution",              timed_node("cypher_query_execution", cypher_query_execution_node))
    builder.add_node("composition_requirement_explanation", timed_node("composition_requirement_explanation", partial(composition_requirement_explanation_node, llm=llm)))
    builder.add_node("intent_graph_update",                 timed_node("intent_graph_update", partial(intent_graph_update_node, llm=llm)))
    builder.add_node("intent_coverage_verifier",            timed_node("intent_coverage_verifier", intent_coverage_verifier_node))
    builder.add_node("candidates_ranking",                  timed_node("candidates_ranking", candidates_ranking_node))
    builder.add_node("graph_to_natural_language",           timed_node("graph_to_natural_language", partial(graph_to_natural_language_node, llm=llm)))
    builder.add_node("intent_aligned_justification",        timed_node("intent_aligned_justification", partial(intent_aligned_justification_node, llm=llm)))
    builder.add_node("recommandantion_baseline",            timed_node("recommandantion_baseline", partial(recommandantion_baseline, llm=llm)))

    # ── Edges ──────────────────────────────────────────────────────────
    builder.add_edge("db_schema_discovery",                 "db_vocabulary")
    builder.add_edge("layer_extraction",                    "category_extraction")
    builder.add_edge("category_extraction",                 "requirements_extraction")
    builder.add_edge("requirements_extraction",             "dimension_inference")
    builder.add_edge("dimension_inference",                 "used_orchestrators_extraction")
    builder.add_edge("used_orchestrators_extraction",       "intent_combination")
    builder.add_edge("intent_combination",                  "intent_graph_generation")
    builder.add_edge("recommandantion_baseline",            END)
    builder.add_edge("intent_graph_generation",             "cypher_query_generation")
    builder.add_edge("cypher_query_generation",             "cypher_query_execution")
    builder.add_edge("composition_requirement_explanation", "intent_graph_update")
    builder.add_edge("intent_coverage_verifier",            "candidates_ranking")
    builder.add_edge("candidates_ranking",                  "graph_to_natural_language")
    builder.add_edge("graph_to_natural_language",           "intent_aligned_justification")
    builder.add_edge("intent_aligned_justification",        END)

    # ── Conditional edges ──────────────────────────────────────────────
    builder.add_conditional_edges(
        START,
        partial(after_start, one_step=one_step, based_on_existing_orchestrator=based_on_existing_orchestrator),
        {
            "recommandantion_baseline": "recommandantion_baseline",
            "db_schema_discovery": "db_schema_discovery",
        },
    )

    builder.add_conditional_edges(
        "db_vocabulary",
        partial(after_db_vocabulary, based_on_existing_orchestrator=based_on_existing_orchestrator),
        {
            "recommandantion_baseline": "recommandantion_baseline",
            "layer_extraction": "layer_extraction",
        },
    )

    builder.add_conditional_edges(
        "cypher_query_execution",
        after_cypher_query_execution,
        {
            "composition_requirement_explanation": "composition_requirement_explanation",
            "intent_coverage_verifier": "intent_coverage_verifier",
        },
    )

    builder.add_conditional_edges(
        "intent_graph_update",
        after_intent_graph_update,
        {
            "cypher_query_generation":  "cypher_query_generation",
            "intent_coverage_verifier": "intent_coverage_verifier",
        },
    )

    return builder.compile(
        checkpointer=MemorySaver(),
        interrupt_before=["intent_graph_update"],
    )