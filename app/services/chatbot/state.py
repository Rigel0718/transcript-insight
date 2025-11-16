from typing import TypedDict, Annotated, Sequence
from langchain.agents import AgentState
from langchain.agents.middleware import AgentMiddleware
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
import operator

class ChatbotState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    cost: Annotated[float, operator.add]


class Middleware(AgentMiddleware):
    state_schema = ChatbotState
    # tools = [tool1, tool2]
    def before_model(self, state: ChatbotState, runtime: ToolRuntime[ContextT]) -> dict[str, Any] | None:
        return super().before_model(state, runtime)


'''
agent = create_agent(
    model,
    tools=tools,
    middleware=[CustomMiddleware()]
)
'''