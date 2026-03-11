import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

from langchain_core.messages import HumanMessage
from orcherstration_recommender.graph import graph


def run(user_query: str, thread_id: str = "thread-1"):

    config = {"configurable": {"thread_id": thread_id}}

    print("\n" + "="*60)
    print(f"USER QUERY: {user_query}")
    print("="*60)

    # ── Initial run ───────────────────────────────────────────────────
    state = graph.invoke(
        {"user_query": user_query, "messages": []},
        config=config,
    )

    print(f"\n[DEBUG status after initial run]: {state.get('status')}")

    # ── Check if graph is waiting for human input ─────────────────────
    if state.get("status") == "waiting_human":
        print("\n[SYSTEM]:", state.get("response_draft", ""))
        print("\nYour response: ", end="")
        user_response = input()

        # ── Add human message to state then resume ────────────────────
        graph.update_state(
            config,
            {"messages": [HumanMessage(content=user_response)]},
        )
        state = graph.invoke(None, config=config)

        print(f"\n[DEBUG status after resume]: {state.get('status')}")
        print(f"[DEBUG recommendation_policy]: {state.get('recommendation_policy')}")
        print(f"[DEBUG attempt_try]: {state.get('attempt_try')}")

    # ── Final response ────────────────────────────────────────────────
    if state.get("status") == "done":
        print("\n[RECOMMENDATION]:")
        print(state.get("final_response", ""))

    elif state.get("status") == "failed":
        print("\n[ERROR]:")
        for error in state.get("errors", []):
            print(f"  - {error}")

    elif state.get("status") == "waiting_human":
        print("\n[SYSTEM still waiting — check graph flow]")

    return state


if __name__ == "__main__":

    # Scenario 1 — Simple case
    # run("I need an open-source orchestrator to deploy my application in the cloud.")

    # Scenario 2 — Edge extension
    # run("We already run Kubernetes in the cloud and want to extend orchestration to edge nodes.")

    # Scenario 3 — Telemedicine composition
    run("I am developing a telemedicine application for connected ambulances...")