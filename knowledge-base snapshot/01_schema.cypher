///////////////////////////////////////////////////////////////////////////
// Knowledge Base (KB) Schema - Neo4j (LPG)
// Purpose: Define naming conventions, node labels, relationships,
//          constraints and indexes.
// Notes:
// - This script does NOT insert the dataset (orchestrators, criteria, etc.)
// - It only defines the "rules of the graph" to keep it consistent.
///////////////////////////////////////////////////////////////////////////

///////////////////////////////////////////////////////////////////////////
// 0.1) ID conventions (recommended)
// - Orchestrator:  O.<slug>   e.g., O.kubernetes, O.kubeedge
// - Layer:         L.<slug>   e.g., L.cloud, L.edge, L.iot, L.continuum
// - Category:      CAT.<slug> e.g., CAT.flow, CAT.service_resource
// - Intent:        INT.<slug> e.g., INT.telemed_composition
// - Dimension:     D.<slug>   e.g., D.impact_adoption
// - Criterion:     C.<slug>   e.g., C.github_stars, C.multi_cloud
///////////////////////////////////////////////////////////////////////////

///////////////////////////////////////////////////////////////////////////
// 0.2) Minimal node properties (recommended)
// Common:
// - id:   unique string (required)
// - name: human-friendly label (recommended)
//
// Orchestrator {id, name, description?, website?, license?}
//
// Layer        {id, name}
//
// Category     {id, name}
//   - name examples: "flow orchestration", "resource & service orchestration"
//
//
// Intent       {id, description?, recommendation_policy?, coverage?,
//               final_recommendation?, attempt_try?, created_at?}
//   - recommendation_policy: e.g., "single_only" | "composition_allowed" | ...
//   - coverage: FULL | PARTIAL | NONE
//   - final_recommendation (enum): SINGLE_TOOL | MULTIPLE_CANDIDATE | TOOL_COMPOSITION | NONE
//   - attempt_try: integer (how many tries)
//
// Dimension    {id, name, description?, depth?}
//   - depth: number of levels in the criterion hierarchy (criterion + subcriteria levels)
//
// Criterion    {id, name, description?, level?}
//   - level: integer, e.g., 1 for criterion, 2+ for subcriteria
//
// IMPORTANT:
// - Keep evaluation values on relationships (SUPPORTS / HAS_METRICS) or as properties
//   on those relationships, rather than duplicating in nodes.
///////////////////////////////////////////////////////////////////////////

///////////////////////////////////////////////////////////////////////////
// 0.3) Relationship vocabulary
// (:Orchestrator)-[:COVERS]->(:Layer)
// (:Orchestrator)-[:HAS_CATEGORY]->(:Category)
// (:Orchestrator)-[:SUPPORTS]->(:Criterion)
// (:Orchestrator)-[:HAS_METRICS]->(:Criterion)
// (:Orchestrator)-[:BASED_ON]->(:Orchestrator)
//
// (:Dimension)-[:HAS_CRITERION]->(:Criterion)
// (:Criterion)-[:HAS_SUBCRITERION]->(:Criterion)
//
// (:Intent)-[:COVERS]->(:Layer)
// (:Intent)-[:REQUIRES]->(:Criterion)
// (:Intent)-[:HAS_CATEGORY]->(:Category)
// (:Intent)-[:CONTEXT_USES]->(:Orchestrator)
///////////////////////////////////////////////////////////////////////////

///////////////////////////////////////////////////////////////////////////
// 0.4) Constraints (UNIQUENESS)
// Neo4j 5+ syntax. Safe to run multiple times.
///////////////////////////////////////////////////////////////////////////

CREATE CONSTRAINT orchestrator_id_unique IF NOT EXISTS
FOR (o:Orchestrator) REQUIRE o.id IS UNIQUE;

CREATE CONSTRAINT layer_id_unique IF NOT EXISTS
FOR (l:Layer) REQUIRE l.id IS UNIQUE;

CREATE CONSTRAINT category_id_unique IF NOT EXISTS
FOR (c:Category) REQUIRE c.id IS UNIQUE;

CREATE CONSTRAINT intent_id_unique IF NOT EXISTS
FOR (i:Intent) REQUIRE i.id IS UNIQUE;

CREATE CONSTRAINT dimension_id_unique IF NOT EXISTS
FOR (d:Dimension) REQUIRE d.id IS UNIQUE;

CREATE CONSTRAINT criterion_id_unique IF NOT EXISTS
FOR (c:Criterion) REQUIRE c.id IS UNIQUE;

///////////////////////////////////////////////////////////////////////////
// 0.5) Helpful indexes (OPTIONAL but useful for performance)
// These are not unique, they speed up lookups by name.
///////////////////////////////////////////////////////////////////////////

CREATE INDEX orchestrator_name_idx IF NOT EXISTS
FOR (o:Orchestrator) ON (o.name);

CREATE INDEX criterion_name_idx IF NOT EXISTS
FOR (c:Criterion) ON (c.name);

CREATE INDEX dimension_name_idx IF NOT EXISTS
FOR (d:Dimension) ON (d.name);

CREATE INDEX intent_name_idx IF NOT EXISTS
FOR (i:Intent) ON (i.name);

///////////////////////////////////////////////////////////////////////////
// 0.6) Relationship properties (your choices)
//
// HAS_METRICS relation:
//   (o)-[m:HAS_METRICS]->(c)
//   m.value: numeric or string

//
// BASED_ON relation:
//   (o1)-[:BASED_ON {type:"fork|extension|inspired"}]->(o2)
//
// REQUIRES relation:
//   (i)-[:REQUIRES {satisfied:true/false}]->(c)
// COVERS relation:
//   (i)-[:COVERS {satisfied:true/false}]->(l)
///////////////////////////////////////////////////////////////////////////

