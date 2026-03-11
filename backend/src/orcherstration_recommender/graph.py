import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from functools import partial

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from orcherstration_recommender.state import State
from orcherstration_recommender.edge import after_cypher_query_execution, after_intent_graph_update

from orcherstration_recommender.nodes.intent_extraction import intent_extraction_node
from orcherstration_recommender.nodes.intent_graph_generation import intent_graph_generation_node
from orcherstration_recommender.nodes.cypher_query_generation import cypher_query_generation_node
from orcherstration_recommender.nodes.cypher_query_execution import cypher_query_execution_node
from orcherstration_recommender.nodes.composition_requirement_explanation import composition_requirement_explanation_node
from orcherstration_recommender.nodes.intent_graph_update import intent_graph_update_node
from orcherstration_recommender.nodes.intent_coverage_verifier import intent_coverage_verifier_node
from orcherstration_recommender.nodes.graph_to_natural_language import graph_to_natural_language_node
from orcherstration_recommender.nodes.intent_aligned_justification import intent_aligned_justification_node

from config.llm_config import LLMConnector


def build_graph():

    # ── LLM ──────────────────────────────────────────────────────────
    llm = LLMConnector()()

    # ── Graph builder ─────────────────────────────────────────────────
    builder = StateGraph(State)

    # ── Nodes ─────────────────────────────────────────────────────────
    builder.add_node("intent_extraction",                   partial(intent_extraction_node, llm=llm))
    builder.add_node("intent_graph_generation",             intent_graph_generation_node)
    builder.add_node("cypher_query_generation",             cypher_query_generation_node)
    builder.add_node("cypher_query_execution",              cypher_query_execution_node)
    builder.add_node("composition_requirement_explanation", partial(composition_requirement_explanation_node, llm=llm))
    builder.add_node("intent_graph_update",                 partial(intent_graph_update_node, llm=llm))
    builder.add_node("intent_coverage_verifier",            intent_coverage_verifier_node)
    builder.add_node("graph_to_natural_language",           partial(graph_to_natural_language_node, llm=llm))
    builder.add_node("intent_aligned_justification",        partial(intent_aligned_justification_node, llm=llm))

    # ── Entry point ───────────────────────────────────────────────────
    builder.set_entry_point("intent_extraction")

    # ── Direct edges ──────────────────────────────────────────────────
    builder.add_edge("intent_extraction",        "intent_graph_generation")
    builder.add_edge("intent_graph_generation",  "cypher_query_generation")
    builder.add_edge("cypher_query_generation",  "cypher_query_execution")
    builder.add_edge("composition_requirement_explanation", "intent_graph_update")
    builder.add_edge("intent_coverage_verifier", "graph_to_natural_language")
    builder.add_edge("graph_to_natural_language", "intent_aligned_justification")
    builder.add_edge("intent_aligned_justification", END)

    # ── Conditional edges ─────────────────────────────────────────────
    builder.add_conditional_edges(
        "cypher_query_execution",
        after_cypher_query_execution,
        {
            "composition_requirement_explanation": "composition_requirement_explanation",
            "intent_coverage_verifier":            "intent_coverage_verifier",
        }
    )

    builder.add_conditional_edges(
        "intent_graph_update",
        after_intent_graph_update,
        {
            "cypher_query_generation": "cypher_query_generation",
            "end":                     END,
        }
    )

    # ── Checkpointer (human-in-the-loop) ──────────────────────────────
    checkpointer = MemorySaver()

    return builder.compile(
        checkpointer=checkpointer,
        interrupt_before=["intent_graph_update"],
    )


graph = build_graph()