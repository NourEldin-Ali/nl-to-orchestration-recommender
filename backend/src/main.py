from langchain_core.messages import HumanMessage
from src.orcherstration_recommender.graph import graph


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
    #run("I need an open-source orchestrator to deploy my application in the cloud.")

    # Scenario 2 — Edge extension
    #run("I am planning to prepare the infrastructure for my cloud application from scratch. I need a cloud orchestrator that supports multi-cloud deployment across AWS and Azure, and that can provision and configure the infrastructure.")

    # Scenario 3 — Telemedicine composition
    #run("I am a doctoral student looking for recent and recognized cloud-edge orchestration frameworks.")


    # Scenario 4
    #run("We already run Kubernetes in the cloud and want to extend orchestration to edge nodes, while supporting deployment, monitoring, and runtime reconfiguration across cloud and edge")


    # Scenario 5
    run("I am developing a telemedicine application for connected ambulances...")

    # Scenario 6
    #run("I want one single tool that handles provisioning, configuration, service orchestration, workflow orchestration, and covers cloud, edge, and IoT.")