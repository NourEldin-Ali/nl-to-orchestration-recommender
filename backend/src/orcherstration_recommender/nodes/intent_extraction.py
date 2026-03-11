import sys
import os
import json
sys.path.append(os.path.join(os.path.dirname(__file__), "../../.."))

from orcherstration_recommender.state import State
from orcherstration_recommender.prompts.prompts_list import INTENT_EXTRACTION_PROMPT
from langchain_core.messages import SystemMessage


def intent_extraction_node(state: State, llm) -> State:
    """
    Component 1 — SLM | Intent Extraction
    Reads  : user_query
    Writes : intent_json {layers, category, requirements, used_orchestrators}
    """
    user_query = state.get("user_query", "")

    messages = [
        SystemMessage(content=INTENT_EXTRACTION_PROMPT.format(user_query=user_query))
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

        intent_json = json.loads(raw)
        print(f"\n[DEBUG intent_json]: {intent_json}")

        return {
            "intent_json": intent_json,
            "status":      "running",
        }

    except json.JSONDecodeError as e:
        return {
            "errors": state.get("errors", []) + [f"intent_extraction_node: JSON parse error: {e}"],
            "status": "failed",
        }
    except Exception as e:
        return {
            "errors": state.get("errors", []) + [f"intent_extraction_node: {e}"],
            "status": "failed",
        }