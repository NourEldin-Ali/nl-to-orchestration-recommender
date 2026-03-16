from langchain_core.messages import HumanMessage

from src.orcherstration_recommender.graph import build_graph


def _print_token_usage(state: dict) -> None:
    token_usage = state.get("token_usage", {})
    totals = token_usage.get("totals", {})
    by_node = token_usage.get("by_node", {})

    if not totals and not by_node:
        print("\n[TOKEN USAGE]: not available from provider metadata")
        return

    print("\n[TOKEN USAGE - TOTAL]")
    print(f"  input_tokens:  {totals.get('input_tokens', 0)}")
    print(f"  output_tokens: {totals.get('output_tokens', 0)}")
    print(f"  total_tokens:  {totals.get('total_tokens', 0)}")

    if by_node:
        print("\n[TOKEN USAGE - BY NODE]")
        for node_name, usage in by_node.items():
            print(
                f"  {node_name}: "
                f"in={usage.get('input_tokens', 0)}, "
                f"out={usage.get('output_tokens', 0)}, "
                f"total={usage.get('total_tokens', 0)}"
            )


def _print_execution_timing(state: dict) -> None:
    timing = state.get("execution_timing", {})
    total_active_seconds = timing.get("total_active_seconds")
    by_node = timing.get("by_node", {})

    if total_active_seconds is None and not by_node:
        print("\n[EXECUTION TIME]: not available")
        return

    print("\n[EXECUTION TIME - TOTAL (EXCLUDING HUMAN WAIT)]")
    print(f"  full_execution_time_seconds: {float(total_active_seconds or 0.0):.4f}")

    if by_node:
        print("\n[EXECUTION TIME - BY NODE]")
        for node_name, data in by_node.items():
            calls = int(data.get("calls", 0))
            last_seconds = float(data.get("last_seconds", 0.0))
            total_seconds = float(data.get("total_seconds", 0.0))
            avg_seconds = float(data.get("avg_seconds", 0.0))
            print(
                f"  {node_name}: "
                f"calls={calls}, "
                f"last={last_seconds:.4f}s, "
                f"total={total_seconds:.4f}s, "
                f"avg={avg_seconds:.4f}s"
            )


def run(
    user_query: str,
    thread_id: str = "thread-1",
    one_step: bool = True,
    based_on_existing_orchestrator: bool = False,
    based_on_exiting_orchestrator: bool | None = None,
):
    if based_on_exiting_orchestrator is not None:
        based_on_existing_orchestrator = based_on_exiting_orchestrator

    config = {"configurable": {"thread_id": thread_id}}

    print("\n" + "=" * 60)
    print(f"USER QUERY: {user_query}")
    print("=" * 60)
    graph = build_graph(
        one_step=one_step,
        based_on_existing_orchestrator=based_on_existing_orchestrator,
    )
    # Initial run
    state = graph.invoke(
        {
            "user_query": user_query,
            "messages": [],
            "one_step": one_step,
            "based_on_existing_orchestrator": based_on_existing_orchestrator,
        },
        config=config,
    )

    print(f"\n[DEBUG status after initial run]: {state.get('status')}")

    # If interrupted for human input, resume graph execution
    if state.get("status") == "waiting_human":
        print("\n[SYSTEM]:", state.get("response_draft", ""))
        print("\nYour response: ", end="")
        user_response = input()

        graph.update_state(
            config,
            {"messages": [HumanMessage(content=user_response)]},
        )
        state = graph.invoke(None, config=config)

        print(f"\n[DEBUG status after resume]: {state.get('status')}")
        print(f"[DEBUG recommendation_policy]: {state.get('recommendation_policy')}")
        print(f"[DEBUG attempt_try]: {state.get('attempt_try')}")

    # Final output
    if state.get("status") == "done":
        print("\n[RECOMMENDATION]:")
        print(state.get("final_response", ""))
        _print_token_usage(state)
        _print_execution_timing(state)

    elif state.get("status") == "failed":
        print("\n[ERROR]:")
        for error in state.get("errors", []):
            print(f"  - {error}")
        _print_token_usage(state)
        _print_execution_timing(state)

    elif state.get("status") == "waiting_human":
        print("\n[SYSTEM still waiting - check graph flow]")
        _print_token_usage(state)
        _print_execution_timing(state)

    return state


if __name__ == "__main__":
    # Scenario 1 - Simple case
    run("I need an open-source orchestrator to deploy my application in the cloud.", one_step=False)

    # Scenario 1 — Simple case
    # run("I need an open-source orchestrator to deploy my application in the cloud.")

    # Scenario 2 — Edge extension
    run(
        "We already run Kubernetes in the cloud and want to extend orchestration to edge nodes.",
        one_step=False,
        based_on_existing_orchestrator=True,
    )

    # Scenario 3 — Telemedicine composition
    #run("I am developing a telemedicine application for connected ambulances...")
