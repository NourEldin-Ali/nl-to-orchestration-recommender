

from src.orcherstration_recommender.state import State


def element_validation_node(state:State, llm):
    """
    LLM-as-Judge
    """
    return {}

def check_element(state:State):
    if True:
        return "graph_generation"
    return "end"