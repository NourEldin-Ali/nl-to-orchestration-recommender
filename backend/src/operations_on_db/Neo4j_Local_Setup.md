# Neo4j Local Setup — Export Aura & Import Docker

This document explains how to export a Neo4j Aura database and import it into a local Docker instance, in order to work offline.

---

## Context

The project uses a **Neo4j Aura** instance (cloud-managed) accessible via:

```
NEO4J_URI=neo4j+s://6d420f67.databases.neo4j.io
```

To work offline, the goal is to replicate this database into a local **Neo4j Docker container**, then connect to it via `bolt://localhost:7687`.

> **Important**: Docker does not connect to Aura. It creates an empty, independent Neo4j instance. Data must be manually exported from Aura and imported into Docker.

---

## Step 1 — Start Neo4j locally with Docker

The `docker-compose.yml` file was updated in two ways:

- `NEO4JLABS_PLUGINS` was renamed to `NEO4J_PLUGINS` (the old name is deprecated since Neo4j 5.0)
- The credentials are loaded from a `.env` file rather than being hardcoded

The `.env` file defines the username and password used by the container:

```env
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=yourpassword
```

> The password cannot be `neo4j` (Neo4j rejects its own default value on startup).

```bash
docker compose up -d
```

---

## Step 2 — Verify that APOC is available on Aura

Aura does not support `neo4j-admin database dump` (reserved for self-hosted instances). The only option for exporting from Aura is **APOC**.

In the Aura browser, verify that APOC is installed:

```cypher
RETURN apoc.version()
```

Expected result: a version number (e.g. `"2026.02.1"`).

---

## Step 3 — Check the database content before exporting

```cypher
MATCH (n) RETURN count(n) as node_count
MATCH ()-[r]->() RETURN count(r) as relationship_count
```

---

## Step 4 — Export the database from Aura using APOC

### Why APOC?

Neo4j Aura is a cloud-managed database: you have no access to the server's filesystem. APOC works around this limitation by returning the exported Cypher directly in the query response via `stream` mode.

### Why the `plain` format?

Two main formats are available:

| Format | Description |
|--------|-------------|
| `cypher-shell` | Includes `:begin`/`:commit` directives to wrap the import in transactions. Requires `cypher-shell` to import. |
| `plain` | Pure Cypher with no transaction directives. Compatible with any Neo4j client. |

For a small database (a few hundred nodes), `plain` is sufficient and much simpler to reimport.

### The export query

```cypher
CALL apoc.export.cypher.all(null, {stream: true, format: "plain"})
YIELD cypherStatements
RETURN cypherStatements
```

- `null` : no file writing (not possible on Aura)
- `stream: true` : returns the result directly in the query response
- `format: "plain"` : pure Cypher, no transaction directives
- `YIELD cypherStatements` : selects the column containing the generated Cypher

### Retrieving the file

In the Aura browser, download the result as **JSON**. The resulting file has the following structure:

```json
[
  {
    "cypherStatements": "CREATE CONSTRAINT ...\nUNWIND [...] AS row\nCREATE ...\n..."
  }
]
```

---

## Step 5 — Import into local Neo4j

The `import_db.py` script handles the import. It is built around three steps:

1. **Read the JSON file** and extract the `cypherStatements` string
2. **Split the Cypher** into individual statements by splitting on `;\n`, filtering out empty strings
3. **Execute each statement** one by one using a Neo4j driver session, logging success or failure for each

The connection is handled by `Neo4jConnector`, which automatically reads credentials from the `.env` file. This keeps the script clean and decoupled from any hardcoded configuration.

> Before running the import, make sure `NEO4J_URI=bolt://localhost:7687` is set in the `.env` (not the Aura URI).

```bash
python3.12 import_db.py
```

---

## Step 6 — Explore the database structure

### Via the Neo4j browser (`http://localhost:7474`)

For an interactive visual overview of the schema:

```cypher
CALL db.schema.visualization()
```

This displays a graph with one node per label and the relationships between them. It is the fastest way to understand the overall structure.

To explore the actual data:

```cypher
-- All orchestrators
MATCH (o:Orchestrator) RETURN o

-- One orchestrator with all its relationships
MATCH (o:Orchestrator)-[r]->(n) RETURN o, r, n

-- Broad graph view (limited to 50 results)
MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 50
```

### Via the Python script `explore_db.py`

The `explore_db.py` script prints the full database structure to the console: labels, relationship types, property keys, node/relationship counts per type, and constraints.

```bash
python3.12 explore_db.py
```

It is useful for automating structure verification after an import, in pipelines, or in tests — contexts where the browser is not available.

---

## Summary

| Step | Tool | Why |
|------|------|-----|
| Start local Neo4j | Docker Compose | Offline instance independent from Aura |
| Verify APOC | Aura browser | Only export method available on Aura |
| Export | APOC stream + plain format | Aura does not expose the filesystem |
| Retrieve | JSON download from Aura browser | More reliable than copy-pasting |
| Import | Python script + Neo4j driver | Reusable and automatable |
| Explore (visual) | Neo4j browser | Interactive visualization |
| Explore (code) | Python script | Automation and logging |