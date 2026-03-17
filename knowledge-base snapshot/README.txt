# Orchestrator Recommendation Knowledge Graph

This repository contains the scripts required to recreate the Knowledge Graph used in our research on **orchestrator recommendation in the Cloud–Edge continuum**.

## Dataset Statistics

- **123 nodes**
- **554 relationships**
- **19 orchestrators**
- **4 evaluation dimensions**
- **94 evaluation criteria**

---

## Requirements

- Neo4j 5.x
- Neo4j Browser

You can run Neo4j using **Neo4j Desktop, Docker, or Neo4j Aura**.

---

## Installation

1. Create an empty Neo4j database.

2. Execute the following scripts **in order**:

```
01_schema.cypher
01_data.cypher
```

These two scripts will create:

- the graph schema
- the taxonomy (dimensions and criteria)
- orchestrator nodes
- evaluation relations and metrics

---

## Verification

To quickly verify that the graph was correctly created:

```cypher
MATCH (n)
RETURN count(n) AS total_nodes;   // should return 123 nodes

MATCH ()-[r]->()
RETURN count(r) AS total_relationships;   // should return 554 relationships
```

---

# Taxonomy Structure

The Knowledge Graph relies on the following **evaluation taxonomy**.

```
Impact & Adoption
 ├── Popularity & Development Activity
 │     ├── open-source code link (GitHub / GitLab)
 │     ├── stars
 │     ├── forks
 │     ├── official documentation link
 │     ├── continuous update
 │
 ├── Scientific Impact
 │     ├── title
 │     ├── year
 │     ├── venue
 │     ├── authors
 │     ├── conference
 │     ├── journal
 │     ├── ranking
 │     ├── number of citations
 │     ├── bibliographic reference
 │
 ├── Supporting Organization
 │     ├── Apache
 │     ├── IBM Foundation
 │     ├── PEPR Cloud


Platform & Integration
 ├── Supported Providers
 │     ├── AWS
 │     ├── Azure
 │     ├── GCP
 │     ├── OpenStack
 │
 ├── Interoperability & Portability
 │     ├── Cross-Cloud
 │     ├── Multi-Cloud
 │     ├── Single Cloud
 │
 ├── Supported Services & Resources
 │     ├── Compute
 │     ├── Storage
 │     ├── Network
 │
 ├── Orchestration Scope
 │     ├── services
 │     ├── resources
 │
 ├── Virtualization Support
 │     ├── VMs
 │     ├── Containers
 │
 ├── User Interface
 │     ├── CLI
 │     ├── API
 │     ├── GUI
 │     ├── AI-assisted


Architecture & Extensibility
 ├── Architecture
 │     ├── Centralized
 │     ├── Decentralized
 │     ├── Hybrid
 │
 ├── Extensibility
 │     ├── extensibility support
 │     ├── documentation availability
 │
 ├── Application Description
 │     ├── Description Type
 │     │     ├── intent-based
 │     │     ├── non-intent based
 │     │           ├── declarative
 │     │           ├── imperative
 │
 │     ├── Structure of the Description
 │     │     ├── machine readable
 │     │     ├── unstructured
 │
 │     ├── Provider Dependency
 │           ├── provider-specific
 │           ├── provider-agnostic
 │
 ├── Language
 │     ├── standard language
 │     ├── proprietary language


Supported Orchestration Operations
 ├── Selection
 │     ├── static
 │     ├── automatic
 │
 ├── Composition
 │     ├── static
 │     ├── automatic
 │
 ├── Provisioning
 ├── Configuration
 ├── Deployment
 ├── Execution & Monitoring
 │
 ├── Runtime Reconfiguration
 │     ├── reactive
 │     ├── proactive
 │     ├── hybrid
```


---
