from typing import Any


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _extract_token_counts(response: Any) -> dict[str, int]:
    usage_metadata = getattr(response, "usage_metadata", None) or {}
    response_metadata = getattr(response, "response_metadata", None) or {}
    provider_usage = {}

    if isinstance(response_metadata, dict):
        provider_usage = response_metadata.get("token_usage") or response_metadata.get("usage") or {}

    input_tokens = (
        _safe_int(usage_metadata.get("input_tokens"))
        or _safe_int(usage_metadata.get("prompt_tokens"))
        or _safe_int(provider_usage.get("input_tokens"))
        or _safe_int(provider_usage.get("prompt_tokens"))
        or _safe_int(response_metadata.get("prompt_eval_count") if isinstance(response_metadata, dict) else 0)
    )

    output_tokens = (
        _safe_int(usage_metadata.get("output_tokens"))
        or _safe_int(usage_metadata.get("completion_tokens"))
        or _safe_int(provider_usage.get("output_tokens"))
        or _safe_int(provider_usage.get("completion_tokens"))
        or _safe_int(response_metadata.get("eval_count") if isinstance(response_metadata, dict) else 0)
    )

    total_tokens = (
        _safe_int(usage_metadata.get("total_tokens"))
        or _safe_int(provider_usage.get("total_tokens"))
        or input_tokens + output_tokens
    )

    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
    }


def add_token_usage(state: dict[str, Any], response: Any, node_name: str) -> dict[str, Any]:
    counts = _extract_token_counts(response)
    existing = state.get("token_usage") or {}

    current_totals = existing.get("totals", {})
    current_by_node = existing.get("by_node", {})
    node_current = current_by_node.get(node_name, {})

    updated_node = {
        "input_tokens": _safe_int(node_current.get("input_tokens")) + counts["input_tokens"],
        "output_tokens": _safe_int(node_current.get("output_tokens")) + counts["output_tokens"],
        "total_tokens": _safe_int(node_current.get("total_tokens")) + counts["total_tokens"],
    }

    updated_by_node = dict(current_by_node)
    updated_by_node[node_name] = updated_node

    updated_totals = {
        "input_tokens": _safe_int(current_totals.get("input_tokens")) + counts["input_tokens"],
        "output_tokens": _safe_int(current_totals.get("output_tokens")) + counts["output_tokens"],
        "total_tokens": _safe_int(current_totals.get("total_tokens")) + counts["total_tokens"],
    }

    return {
        "totals": updated_totals,
        "by_node": updated_by_node,
    }
