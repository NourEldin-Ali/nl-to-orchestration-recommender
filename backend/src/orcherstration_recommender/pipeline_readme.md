# Graph, Edges & State — Intent-Driven Orchestration Recommendation System

---

## State

The state is a `TypedDict` that flows through the entire pipeline. Every node reads from and writes to this shared state.
```python
class State(TypedDict, total=False):

    # ── Conversation history ──────────────────────────────────────────
    messages: Annotated[List[AnyMessage], add_messages]

    # ── DB Discovery ─────────────────────────────────────────────────
    db_schema:          list        # [(from, relation, to), ...]
    db_vocabulary:      dict        # {layers, categorys, criterions, orchestrators, ...}

    # ── Intent Construction ───────────────────────────────────────────
    user_query:                  str
    detected_layers:             list
    detected_category:           str
    detected_requirements:       list
    detected_used_orchestrators: list
    intent_json:                 dict   # {layers, category, requirements, used_orchestrators}

    # ── Intent Graph (Neo4j) ──────────────────────────────────────────
    intent_id:              str    # UUID of the Intent node in Neo4j
    intent_graph_created:   bool

    # ── Intent Node Attributes ────────────────────────────────────────
    recommendation_policy:  str    # single_only | composition_allowed | composition_not_allowed
    attempt_try:            int
    coverage:               str    # FULL | PARTIAL | NONE
    final_recommendation:   str    # SingleCandidate | MultipleCandidates | CompositionOfTools | None

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
    status:                 str    # running | waiting_human | done | failed
    errors:                 List[str]
```

### State lifecycle

| Phase | Keys written |
|---|---|
| DB Discovery | `db_schema`, `db_vocabulary` |
| Intent Extraction | `detected_layers`, `detected_category`, `detected_requirements`, `detected_used_orchestrators`, `intent_json` |
| Intent Graph | `intent_id`, `intent_graph_created`, `recommendation_policy`, `attempt_try` |
| Cypher Engine | `minimal_cypher_query`, `minimal_subgraph`, `enriched_cypher_query`, `enriched_subgraph` |
| Composition Handler | `response_draft`, `status`, `recommendation_policy`, `attempt_try` |
| Coverage Verification | `coverage_annotated_intent`, `coverage`, `final_recommendation` |
| Final Explanation | `response_draft`, `final_response`, `status` |

---

## Graph

The graph is built using **LangGraph** `StateGraph` with a `MemorySaver` checkpointer to support human-in-the-loop interrupts.

### Entry point
`db_schema_discovery`

### Full node sequence
```
db_schema_discovery
    → db_vocabulary
        → layer_extraction
            → category_extraction
                → requirements_extraction
                    → used_orchestrators_extraction
                        → intent_combination
                            → intent_graph_generation
                                → cypher_query_generation
                                    → cypher_query_execution
                                        ↓ (conditional)
                            ┌───────────────────────────────────────┐
                            │ empty result + attempt_try == 1        │
                            │   → composition_requirement_explanation│
                            │       → [INTERRUPT]                    │
                            │       → intent_graph_update            │
                            │           ↓ (conditional)              │
                            │   composition_not_allowed → END        │
                            │   composition_allowed                  │
                            │       → cypher_query_generation        │
                            └───────────────────────────────────────┘
                                        ↓ (non-empty result)
                                    intent_coverage_verifier
                                        → graph_to_natural_language
                                            → intent_aligned_justification
                                                → END
```

### Interrupt
The graph is compiled with:
```python
interrupt_before=["intent_graph_update"]
```
This pauses execution before `intent_graph_update` to wait for the user's response to the composition explanation. The main loop in `main.py` handles this by updating the state with the human message and resuming.

---

## Edges

### Direct edges

| From | To | Description |
|---|---|---|
| `db_schema_discovery` | `db_vocabulary` | Schema discovered → extract vocabulary |
| `db_vocabulary` | `layer_extraction` | Vocabulary ready → start intent extraction |
| `layer_extraction` | `category_extraction` | Layers detected → extract category |
| `category_extraction` | `requirements_extraction` | Category detected → extract requirements |
| `requirements_extraction` | `used_orchestrators_extraction` | Requirements detected → extract used orchestrators |
| `used_orchestrators_extraction` | `intent_combination` | All components detected → combine into intent_json |
| `intent_combination` | `intent_graph_generation` | intent_json ready → create Intent node in Neo4j |
| `intent_graph_generation` | `cypher_query_generation` | Intent graph created → generate Cypher query |
| `cypher_query_generation` | `cypher_query_execution` | Query ready → execute against Neo4j |
| `composition_requirement_explanation` | `intent_graph_update` | User informed → wait for response then update |
| `intent_coverage_verifier` | `graph_to_natural_language` | Coverage computed → transform to natural language |
| `graph_to_natural_language` | `intent_aligned_justification` | Draft ready → generate final response |
| `intent_aligned_justification` | `END` | Final response produced → end pipeline |

### Conditional edges

#### `after_cypher_query_execution`
Triggered after `cypher_query_execution`.
```python
if minimal_subgraph is empty AND attempt_try == 1:
    → composition_requirement_explanation
else:
    → intent_coverage_verifier
```

| Condition | Next node |
|---|---|
| No result found + first attempt | `composition_requirement_explanation` |
| Result found OR second attempt | `intent_coverage_verifier` |

#### `after_intent_graph_update`
Triggered after `intent_graph_update`.
```python
if recommendation_policy == "composition_not_allowed":
    → END
else:
    → cypher_query_generation
```

| Condition | Next node |
|---|---|
| User refused composition | `END` |
| User accepted composition | `cypher_query_generation` (re-run with updated policy) |