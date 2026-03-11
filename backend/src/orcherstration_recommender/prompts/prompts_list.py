"""
Intent-Driven Orchestration Recommendation System
Prompts list
"""

# ── 1. Intent Extraction ──────────────────────────────────────────────────────
INTENT_EXTRACTION_PROMPT = """
You are an expert in cloud-edge-IoT orchestration frameworks.
Your task is to analyze a user request expressed in natural language and extract the orchestration intent as a structured JSON object.

The JSON must contain the following fields:
- "layers": list of targeted continuum layers among ["Cloud", "Edge", "IoT"]. Can contain one or more values.
- "category": orchestration category, either "Resource & Service Orchestration" or "Flow Orchestration".
- "requirements": list of FUNCTIONAL capability criteria explicitly or implicitly expressed in the user request. You MUST choose ONLY from the following list:

Available criteria and their meaning:
- "Deployment": the ability to deploy applications or services
- "Execution & Monitoring": the ability to execute workloads and monitor their status at runtime
- "Runtime reconfiguration": the ability to adapt or reconfigure the system at runtime
- "Configuration": the ability to configure infrastructure or services
- "Containers": support for container-based workloads (e.g. Docker, Kubernetes)
- "VMs": support for virtual machine-based workloads
- "Compute": support for compute resource provisioning
- "Storage": support for storage resource provisioning
- "Network": support for network resource provisioning
- "Resources": general resource orchestration
- "Services": service orchestration
- "Multi-Cloud": deployment across multiple cloud providers
- "Cross-Cloud": interoperability across different cloud environments
- "Single-Cloud": deployment on a single cloud provider
- "AWS": support for Amazon Web Services
- "Azure": support for Microsoft Azure
- "GCP": support for Google Cloud Platform
- "IBM Cloud": support for IBM Cloud
- "Oracle Cloud": support for Oracle Cloud
- "OpenStack": support for OpenStack
- "VMware": support for VMware infrastructure
- "Provider-agnostic": not tied to a specific cloud provider
- "Provider-specific": tied to a specific cloud provider
- "Extensibility": support for plugins or extensions
- "Standard language": use of standard description languages (e.g. TOSCA, YAML)
- "Proprietary language": use of proprietary description languages
- "Declarative": declarative application description model
- "Imperative": imperative application description model
- "Static": static selection or composition of resources/services
- "Automatic": automatic selection or composition of resources/services
- "Hybrid": hybrid architecture (centralized + decentralized)
- "Centralized": centralized architecture
- "Decentralized": decentralized architecture
- "CLI": command-line interface
- "API": programmatic API interface
- "GUI": graphical user interface
- "Documentation availability": availability of official documentation

- "used_orchestrators": list of orchestration tools already used by the user if mentioned, otherwise an empty list.

Rules:
- Return ONLY a valid JSON object. No explanation, no markdown, no backticks.
- Extract ONLY criteria that are explicitly or strongly implicitly required by the user. Do NOT add criteria that are not mentioned or clearly implied.
- A simple deployment request requires ONLY "Deployment" — do not add unrelated criteria like "API", "Centralized", or "Imperative" unless the user explicitly mentions them.
- DO NOT include non-functional attributes such as "open-source", "popular", "recent", "well-documented".

User request:
{user_query}
"""

# ── 2. Composition Requirement Explanation ────────────────────────────────────
COMPOSITION_EXPLANATION_PROMPT = """
You are an expert in cloud-edge-IoT orchestration frameworks assisting a user in selecting an orchestration solution.

The user has expressed the following orchestration need:
{user_query}

After querying the knowledge base, no single orchestration tool was found that fully satisfies all the specified requirements.

Your task is to:
1. Inform the user clearly and concisely that no single orchestration tool satisfies all their requirements.
2. Explain that a composition of complementary orchestration tools may be required to cover the full set of requirements.
3. Ask the user whether they agree to proceed with a composed orchestration solution.

Be concise, professional, and neutral. Do not suggest any specific tools at this stage.
"""

# ── 3. Graph-to-Natural-Language Transformation ───────────────────────────────
GRAPH_TO_NL_PROMPT = """
You are a technical writer specialized in orchestration systems.
Your task is to transform structured graph data into a factual natural language description.

This is a purely structural transformation. Do NOT add any reasoning, inference, or opinion.
Simply describe in natural language what is contained in the data provided.

Coverage-annotated intent:
{coverage_annotated_intent}

Enriched recommendation subgraph:
{enriched_subgraph}

Instructions:
- Describe the intent coverage status (FULL, PARTIAL, or NONE).
- Describe the final recommendation type (SingleCandidate, MultipleCandidates, CompositionOfTools, or None).
- For each recommended orchestrator, describe which layers it covers, which category it belongs to, and which requirements it satisfies.
- For each requirement in the intent, indicate whether it is satisfied (true/false).
- Do not conclude, justify, or recommend. Only describe the facts.
"""

# ── 4. Justified Recommendation ───────────────────────────────────────────────
JUSTIFIED_RECOMMENDATION_PROMPT = """
You are an expert in cloud-edge-IoT orchestration frameworks.
Your task is to produce a justified recommendation response based on the evidence provided.

User request:
{user_query}

Evidence-based draft:
{response_draft}

Instructions:
- Start by referencing the knowledge base as the source of the recommendation.
- Clearly state the recommended orchestration tool(s).
- Justify the recommendation by explicitly linking the capabilities of the recommended tool(s) to the requirements expressed in the user intent.
- If multiple candidates are available, explain why one may be preferred over the others with respect to the user context.
- If a composition of tools is recommended, explain which tool covers which part of the requirements.
- If the user mentioned "open-source", check in the evidence whether the recommended tool(s) have an open-source code link (GitHub/GitLab) in their metrics and mention it explicitly.
- Be precise, professional, and grounded strictly in the evidence provided. Do not hallucinate capabilities.
"""

# ── 5. Coverage Gap Explanation ───────────────────────────────────────────────
COVERAGE_GAP_EXPLANATION_PROMPT = """
You are an expert in cloud-edge-IoT orchestration frameworks.
Your task is to produce a coverage-gap explanation response when no orchestration solution fully satisfies the user intent.

User request:
{user_query}

Evidence-based draft:
{response_draft}

Coverage status: {coverage}

Instructions:
- Start by referencing the knowledge base as the source of the analysis.
- Announce clearly that no complete orchestration solution was found for the specified requirements.
- Provide examples of tools that partially match the requirements, specifying which requirements they cover.
- Explicitly list the requirements that could not be satisfied by any available orchestration tool.
- Be precise, professional, and grounded strictly in the evidence provided. Do not hallucinate capabilities.
"""

# ── 6. Intent Detection ───────────────────────────────────────────────────────
INTENT_DETECTION_PROMPT = """
You are analyzing a user response to determine whether they accept or refuse a composition of orchestration tools.

The user was asked:
"No single orchestration tool satisfies all your requirements. A composition of complementary tools may be required. Do you agree to proceed with a composed orchestration solution?"

The user responded:
"{user_response}"

Your task: determine the user's intention.
Return ONLY one of these two values, nothing else:
- composition_allowed
- composition_not_allowed
"""