from langgraph.graph import START,END, StateGraph
from src.orcherstration_recommender.state import State
from src.config.llm_config import LLMConnector

from src.orcherstration_recommender.nodes.element_extraction_node import element_extraction_node
from src.orcherstration_recommender.nodes.intent_graph_generation_node import intent_graph_generation_node
from src.orcherstration_recommender.nodes.knowledge_graph_extraction_node import check_sub_graph, knowledge_graph_extraction_node
from src.orcherstration_recommender.nodes.element_validation_node import check_element, element_validation_node
from src.orcherstration_recommender.nodes.intent_observation_node import intent_observation_node
from src.orcherstration_recommender.nodes.intent_verification_node import intent_verification_node


class RecommenderAgent:
    def __init__(self):
        # load LLM
        llm = LLMConnector()()
        
        builder = StateGraph(state_schema=State)
        builder.add_node("element_extraction", lambda input: element_extraction_node(input, llm))
        builder.add_node("element_validation", lambda input: element_validation_node(input, llm))
        builder.add_node("graph_generation", lambda input: intent_graph_generation_node(input))
        builder.add_node("knowledge_graph", lambda input: knowledge_graph_extraction_node(input))
        builder.add_node("intent_verification", lambda input: intent_verification_node(input))
        builder.add_node("intent_observation", lambda input: intent_observation_node(input))


        builder.add_edge(START, "element_extraction")
        builder.add_edge("element_extraction", "element_validation")
        
        builder.add_conditional_edges(
            "element_validation",
            lambda input: check_element(input),
            {
                "graph_generation": "graph_generation",
                "end": END,
            },
        )

        builder.add_conditional_edges(
            "graph_generation",
            lambda input: check_sub_graph(input),
            {
                "user_validation": "element_extraction",
                "intent_verification": "intent_verification",
            },
        )

        builder.add_edge("intent_verification", "intent_observation")
        builder.add_edge("intent_observation", END)

        self.graph = builder.compile()
    
    def invoke(self, args):
        """Invoke the agent with the given arguments.
        
        Args:
            args: it is a dict that contains the input for the agent. The keys of the dict should match the input keys defined in the state schema.
        """
        result = self.graph.invoke(args)

        schema_result = result.get("schema_result") # extract the schema result from the state
        print("Schema Result:", schema_result)
        return schema_result