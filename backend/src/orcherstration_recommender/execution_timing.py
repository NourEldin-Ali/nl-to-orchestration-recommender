from typing import Any


def _safe_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def add_execution_timing(state: dict[str, Any], node_name: str, elapsed_seconds: float) -> dict[str, Any]:
    existing = state.get("execution_timing") or {}
    by_node = existing.get("by_node", {})
    node_current = by_node.get(node_name, {})

    calls = _safe_int(node_current.get("calls")) + 1
    total_seconds = _safe_float(node_current.get("total_seconds")) + elapsed_seconds
    avg_seconds = total_seconds / calls if calls else 0.0

    updated_by_node = dict(by_node)
    updated_by_node[node_name] = {
        "calls": calls,
        "last_seconds": elapsed_seconds,
        "total_seconds": total_seconds,
        "avg_seconds": avg_seconds,
    }

    total_active_seconds = _safe_float(existing.get("total_active_seconds")) + elapsed_seconds

    return {
        "total_active_seconds": total_active_seconds,
        "full_execution_time_seconds": total_active_seconds,
        "by_node": updated_by_node,
    }
