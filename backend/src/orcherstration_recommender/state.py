from typing import Annotated, List, Optional
from typing_extensions import TypedDict
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


class State(TypedDict, total=False):

    # ── Conversation history ──────────────────────────────────────────
    messages: Annotated[List[AnyMessage], add_messages]

    # ── Intent (SLM - étape 1) ────────────────────────────────────────
    user_query:             str
    intent_json:            dict        # {layers, category, requirements, used_orchestrators}
    intent_id:              str         # UUID unique par intent (clé Neo4j)
    intent_graph_created:   bool

    # ── Attributs du nœud Intent ──────────────────────────────────────
    recommendation_policy:  str         # single_only | composition_allowed | composition_not_allowed
    attempt_try:            int
    coverage:               str         # FULL | PARTIAL | NONE
    final_recommendation:   str         # SingleCandidate | MultipleCandidates | CompositionOfTools | None

    # ── Reasoner (étape 2) ────────────────────────────────────────────
    minimal_cypher_query:   str
    minimal_subgraph:       list
    enriched_cypher_query:  str
    enriched_subgraph:      list

    # ── Coverage ──────────────────────────────────────────────────────
    coverage_annotated_intent: dict     # intent graph annoté avec satisfied par relation

    # ── Output ────────────────────────────────────────────────────────
    response_draft:         str
    final_response:         str

    # ── Control flow ──────────────────────────────────────────────────
    status:                 str         # running | waiting_human | done | failed
    errors:                 List[str]