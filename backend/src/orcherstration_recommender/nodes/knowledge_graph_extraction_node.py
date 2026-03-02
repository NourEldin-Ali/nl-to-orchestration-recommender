from src.orcherstration_recommender.state import State


def knowledge_graph_extraction_node(state:State):
    """
    Call Graph DB, without LLM for now
    """
    return {}

def check_sub_graph(state:State):
    """
    Check if it is mix to ask you to validation
    """
    if True:
        return "intent_verification"
    return "user_validation"