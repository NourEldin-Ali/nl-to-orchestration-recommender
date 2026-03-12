from typing import Annotated, List, Optional
from typing_extensions import TypedDict
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


class State(TypedDict, total=False):

    # ── Conversation history ──────────────────────────────────────────
    messages: Annotated[List[AnyMessage], add_messages]

    # ── DB Discovery ─────────────────────────────────────────────────
    db_schema:          list        # [(Label)-[:RELATION]->(Label), ...]
    db_vocabulary:      dict        # {layers, categories, criteria, orchestrators}

    # ── Intent Construction (successive extraction) ───────────────────
    user_query:             str
    detected_layers:        list        # output node 1
    detected_category:      str         # output node 2
    detected_requirements:  list        # output node 3
    detected_used_orchestrators: list   # output node 4
    intent_json:            dict        # {layers, category, requirements, used_orchestrators} — assemblé algo

    # ── Intent Graph (Neo4j) ──────────────────────────────────────────
    intent_id:              str         # UUID unique par intent
    intent_graph_created:   bool

    # ── Attributs du nœud Intent ──────────────────────────────────────
    recommendation_policy:  str         # single_only | composition_allowed | composition_not_allowed
    attempt_try:            int
    coverage:               str         # FULL | PARTIAL | NONE
    final_recommendation:   str         # SingleCandidate | MultipleCandidates | CompositionOfTools | None

    # ── Reasoner ──────────────────────────────────────────────────────
    minimal_cypher_query:   str
    minimal_subgraph:       list
    enriched_cypher_query:  str
    enriched_subgraph:      list

    # ── Coverage ──────────────────────────────────────────────────────
    coverage_annotated_intent: dict

    # ── Output ────────────────────────────────────────────────────────
    response_draft:         str
    final_response:         str

    # ── Control flow ──────────────────────────────────────────────────
    status:                 str         # running | waiting_human | done | failed
    errors:                 List[str]