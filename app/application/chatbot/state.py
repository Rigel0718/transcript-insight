from typing import TypedDict, Annotated, Sequence
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
import operator

class ChatbotState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    cost: Annotated[float, operator.add]

