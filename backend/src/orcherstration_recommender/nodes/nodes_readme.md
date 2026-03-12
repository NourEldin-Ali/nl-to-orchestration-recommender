# Nodes — Intent-Driven Orchestration Recommendation System

This folder contains all the nodes of the LangGraph pipeline. Each node is a self-contained Python module responsible for a specific step in the recommendation process. Nodes are either **algorithmic (no LLM)** or **LLM-based**.

---

## DB Discovery Nodes

### `db_schema_discovery.py`
**Type**: Algorithmic — no LLM  
**Component**: DB Discovery — Node 1

**Role**: Discovers the structure of the Neo4j knowledge base by querying all distinct relationships between node labels. This is the very first node that runs in the pipeline — it has no dependency on any previous state.

**How it works**:
Executes the following query on Neo4j:
```cypher
MATCH (a)-[r]->(b)
RETURN DISTINCT labels(a)[0] AS from, type(r) AS relation, labels(b)[0] AS to
```
Filters out any entry where `from` or `to` is `Intent` to avoid pollution from previous runs.

---

### `db_vocabulary_construction.py`
**Type**: Algorithmic — no LLM  
**Component**: DB Discovery — Node 2

**Role**: Extracts all distinct named values for each label discovered in `db_schema`. Produces the **consultation table** used by all downstream LLM nodes to ground their extractions in exact db values.

**How it works**:
- Iterates over all labels found in `db_schema`
- For each label, runs:
```cypher
MATCH (n:Label)
WHERE n.name IS NOT NULL
RETURN DISTINCT n.name AS name
ORDER BY n.name
```
- Excludes the `Intent` label entirely
- Stores results as `{label_lowercase + "s": [values]}`

---

## Intent Extraction Nodes

These nodes work **successively**: each node contextualizes the next by passing its output forward through the state.

### `layer_extraction.py`
**Type**: LLM-based  
**Component**: Intent Extraction — Node 1

**Role**: Identifies the targeted continuum layers from the user request.

**How it works**:
Sends `user_query` and the list of available layers from `db_vocabulary` to the LLM using `LAYER_EXTRACTION_PROMPT`. The LLM returns a JSON with the detected layers chosen strictly from the available list.

---

### `category_extraction.py`
**Type**: LLM-based  
**Component**: Intent Extraction — Node 2

**Role**: Identifies the orchestration category from the user request, contextualized by the already detected layers.

**How it works**:
Sends `user_query`, `detected_layers`, and the list of available categories from `db_vocabulary` to the LLM using `CATEGORY_EXTRACTION_PROMPT`. The LLM returns a JSON with the detected category chosen strictly from the available list, or `null` if none matches.

---

### `requirements_extraction.py`
**Type**: LLM-based  
**Component**: Intent Extraction — Node 3

**Role**: Identifies the functional capability criteria required by the user, contextualized by the detected layers and category.

**How it works**:
Sends `user_query`, `detected_layers`, `detected_category`, and the full list of available criteria from `db_vocabulary` to the LLM using `REQUIREMENTS_EXTRACTION_PROMPT`. The LLM returns a JSON with the detected requirements chosen strictly from the available list.

The prompt explicitly forbids:
- Using orchestrator names as requirements (e.g. Kubernetes, KubeEdge)
- Using layer names as requirements (e.g. Cloud, Edge)
- Using category names as requirements
- Inventing values not present in the available criteria list

---

### `used_orchestrators_extraction.py`
**Type**: LLM-based  
**Component**: Intent Extraction — Node 4

**Role**: Identifies orchestration tools already used or mentioned by the user, using the full intent context accumulated so far.

**How it works**:
Sends `user_query`, `detected_layers`, `detected_category`, `detected_requirements`, and the list of available orchestrators from `db_vocabulary` to the LLM using `USED_ORCHESTRATORS_EXTRACTION_PROMPT`. The LLM returns a JSON with the orchestrators explicitly mentioned by the user as already in use, or an empty list.

---

### `intent_extraction.py`
**Type**: Algorithmic — no LLM  
**Component**: Intent Extraction — Node 5 (Combination)

**Role**: Combines the four extracted intent components into a single structured `intent_json` object. Pure assembly — no LLM involved.

**How it works**:
Simply reads `detected_layers`, `detected_category`, `detected_requirements`, `detected_used_orchestrators` from the state and assembles them into:
```python
{
    "layers": [...],
    "category": "...",
    "requirements": [...],
    "used_orchestrators": [...]
}
```

---

## Intent Graph Generation

### `intent_graph_generation.py`
**Type**: Algorithmic — no LLM  
**Component**: Component 1 — SLM

**Role**: Creates an `Intent` node in the Neo4j knowledge base and connects it to the existing nodes using relationships discovered dynamically from `db_schema`.

**How it works**:
1. Creates the `Intent` node with attributes: `id`, `user_query`, `recommendation_policy` (default: `single_only`), `attempt_try` (default: `1`), `coverage` (null), `final_recommendation` (null)
2. For each layer in `intent_json.layers` → `MATCH` existing `Layer` node → `CREATE (i)-[:COVERS]->(l)`
3. For `intent_json.category` → `MATCH` existing `Category` node → `CREATE (i)-[:HAS_CATEGORY]->(c)`
4. For each requirement → `MATCH` existing `Criterion` node → `CREATE (i)-[:REQUIRES]->(cr)`
5. For each used orchestrator → `MATCH` existing `Orchestrator` node → `CREATE (i)-[:BASED_ON]->(o)`

Uses `MATCH` (not `MERGE`) for all existing nodes to avoid creating parasitic nodes in the db. All relationship names are dynamically extracted from `db_schema`.

---

## Cypher Query Engine

### `cypher_query_generation.py`
**Type**: Algorithmic — no LLM  
**Component**: Component 2 — Reasoner

**Role**: Builds the minimal Cypher query from the intent requirements. All relationships used in the query are dynamically extracted from `db_schema`.

**How it works**:
1. Extracts relations from `db_schema` (COVERS, HAS_CATEGORY, SUPPORTS, BASED_ON)
2. Builds MATCH clauses for each layer, category and requirement
3. If `recommendation_policy = composition_allowed`, extends the category condition to also include `Flow Orchestration`
4. If `used_orchestrators` is specified, adds an ORDER BY clause to prioritize compatible tools
5. Returns a minimal query that only returns the `Orchestrator` node(s)

---

### `cypher_query_execution.py`
**Type**: Algorithmic — no LLM  
**Component**: Component 2 — Reasoner

**Role**: Executes the minimal Cypher query. If results are found, builds and executes an enriched query that retrieves all relationships of the candidate orchestrators.

**How it works**:
1. Executes the minimal query → gets `minimal_subgraph`
2. If empty → returns immediately (triggers composition handler via conditional edge)
3. If not empty → builds enriched query dynamically from `db_schema` by adding `OPTIONAL MATCH` clauses for all outgoing relations from `Orchestrator`
4. Executes the enriched query → parses results dynamically into `enriched_subgraph`

---

## Composition Handler

### `composition_requirement_explanation.py`
**Type**: LLM-based  
**Component**: Component 1 — SLM

**Role**: Triggered when `minimal_subgraph` is empty and `attempt_try == 1`. Informs the user that no single orchestration tool satisfies all requirements and asks whether to proceed with a composed solution.

**How it works**:
Sends `user_query` to the LLM using `COMPOSITION_EXPLANATION_PROMPT`. The LLM generates a professional, neutral message explaining the situation and asking for user confirmation. Sets `status = waiting_human` to trigger the human-in-the-loop interrupt.

---

### `intent_graph_update.py`
**Type**: LLM-based  
**Component**: Component 1 — SLM

**Role**: Triggered after the user responds to the composition explanation. Classifies the user response and updates the Intent node in Neo4j accordingly.

**How it works**:
1. Extracts the last human message from `messages`
2. Sends it to the LLM using `INTENT_DETECTION_PROMPT` to classify as `composition_allowed` or `composition_not_allowed`
3. Updates the Intent node in Neo4j: sets `recommendation_policy` and increments `attempt_try`
4. If `composition_allowed`: finds the exact `Flow Orchestration` category value from `db_vocabulary` and adds a `HAS_CATEGORY` relation to the Intent node using the relation name from `db_schema`

---

## Intent Coverage Verification

### `intent_coverage_verifier.py`
**Type**: Algorithmic — no LLM  
**Component**: Component 2 — Reasoner

**Role**: Evaluates the coverage of the user intent by comparing each intent relation against the enriched recommendation subgraph.

**How it works**:
1. Extracts relation names dynamically from `db_schema` (covers, has_category, supports)
2. Collects all values present in `enriched_subgraph` for layers, categories and criteria
3. For each intent element (layers, category, requirements), checks if it is satisfied by at least one orchestrator in the subgraph
4. Annotates each element with `satisfied: true/false`
5. Computes overall coverage: `FULL` (all satisfied), `PARTIAL` (some satisfied), `NONE` (none satisfied)
6. Determines `final_recommendation` based on number of orchestrators and `recommendation_policy`
7. Updates the Intent node in Neo4j with `coverage` and `final_recommendation`

---

## Final Explanation Generation

### `graph_to_natural_language.py`
**Type**: LLM-based  
**Component**: Component 1 — SLM

**Role**: Performs a **purely structural transformation** of the coverage-annotated intent and the enriched recommendation subgraph into natural language. No reasoning or inference — only describes what is in the data.

**How it works**:
Sends `coverage_annotated_intent` and `enriched_subgraph` (both serialized as JSON) to the LLM using `GRAPH_TO_NL_PROMPT`. The LLM describes factually: coverage status, final recommendation type, which orchestrators cover which layers/categories/criteria, and which requirements are satisfied or not.

---

### `intent_aligned_justification.py`
**Type**: LLM-based  
**Component**: Component 1 — SLM

**Role**: Generates the final response presented to the user. Selects the appropriate prompt based on coverage status.

**How it works**:
- If `coverage = FULL` → uses `JUSTIFIED_RECOMMENDATION_PROMPT`: produces a justified recommendation grounded in the knowledge base, explicitly linking tool capabilities to user requirements
- If `coverage = PARTIAL` or `NONE` → uses `COVERAGE_GAP_EXPLANATION_PROMPT`: explains what was and was not satisfied, provides examples of partial matches, lists unsatisfied requirements