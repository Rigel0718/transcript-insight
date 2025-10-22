from app.services.chatbot.chatbot_node import ChatbotNode
from langgraph.checkpoint.memory import MemorySaver
from app.services.chatbot.state import ChatbotState
from langgraph.graph.state import CompiledStateGraph
from queue import Queue
from app.core.env_model import Env
from langgraph.graph import StateGraph, START, END


def chatbot(verbose: bool = False, track_time: bool = False, queue: Queue=None, env: Env=None) -> CompiledStateGraph:
    chatbot_node = ChatbotNode(verbose=verbose, track_time=track_time, queue=queue, env=env)
    graph = StateGraph(state_type=ChatbotState)
    graph.add_node("chatbot", chatbot_node)
    graph.add_edge(START, "chatbot")
    graph.add_edge("chatbot", END)
    memory_saver = MemorySaver()
    return graph.compile(checkpoint=memory_saver)


