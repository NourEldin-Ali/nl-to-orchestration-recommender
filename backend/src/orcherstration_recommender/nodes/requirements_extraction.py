import json
from src.orcherstration_recommender.state import State
from src.orcherstration_recommender.prompts.prompts_list import REQUIREMENTS_EXTRACTION_PROMPT
from langchain_core.messages import SystemMessage


def requirements_extraction_node(state: State, llm) -> State:
    """
    Intent Extraction — Node 3 | Requirements Extraction
    Reads  : user_query, db_vocabulary, detected_layers, detected_category
    Writes : detected_requirements
    """
    user_query        = state.get("user_query", "")
    db_vocabulary     = state.get("db_vocabulary", {})
    detected_layers   = state.get("detected_layers", [])
    detected_category = state.get("detected_category", "")
    criteria          = db_vocabulary.get("criterions", [])

    messages = [
        SystemMessage(content=REQUIREMENTS_EXTRACTION_PROMPT.format(
            user_query=user_query,
            detected_layers=json.dumps(detected_layers),
            detected_category=detected_category,
            criteria=json.dumps(criteria, indent=2),
        ))
    ]

    try:
        response = llm.invoke(messages)
        raw = response.content.strip()

        if raw.startswith("```json"):
            raw = raw[7:]
        elif raw.startswith("```"):
            raw = raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()

        result = json.loads(raw)
        detected_requirements = result.get("requirements", [])

        print(f"\n[DEBUG detected_requirements]: {detected_requirements}")

        return {
            "detected_requirements": detected_requirements,
            "status":                "running",
        }

    except Exception as e:
        return {
            "errors": state.get("errors", []) + [f"requirements_extraction_node: {e}"],
            "status": "failed",
        }