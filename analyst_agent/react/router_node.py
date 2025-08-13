from typing import Literal, Optional
from pydantic import BaseModel, Field
from analyst_agent.react.base import BaseNode
from analyst_agent.react.state import AgentContextState
from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel
from analyst_agent.react.utils import load_prompt_template

class RouteDecision(BaseModel):
    action: Literal["to_gen_df", "to_gen_chart", "finish"] = Field(
        ..., description="Next action for the agent."
    )
    reason: str = Field(..., description="One concise sentence explaining the decision.")
    notes: Optional[str] = None


class RouterNode(BaseNode):
    def __init__(self, llm: Optional[BaseChatModel] = None, verbose=False, **kwargs):
        super().__init__(verbose=verbose, **kwargs)
        self.llm = llm or self._init_llm()
    
    def _init_llm(self):
        llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0,
        )
        return llm 
    
    def run(self, state: AgentContextState) -> AgentContextState:
        prompt = load_prompt_template("prompts/router.yaml")
        chain = prompt | self.llm.with_structured_output(RouteDecision)
        user_query = state['user_query']
        current_dataframe_informs = state['current_dataframe']
        current_chart_informs = state['current_chart']
        input_values = {
            'user_query': user_query, 
            'current_dataframe_informs': current_dataframe_informs, 
            'current_chart_informs': current_chart_informs,
            'previous_node': state['previous_node']
            }
        
        result: RouteDecision = chain.invoke(input_values)
        return {'next_action': result.action, 'previous_node': 'router'}

