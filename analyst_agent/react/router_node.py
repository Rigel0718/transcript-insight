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
            model="gpt-4o-mini",
            temperature=0,
        )
        return llm 
    
    def run(self, state: AgentContextState) -> AgentContextState:
        try:
            prompt = load_prompt_template("prompts/router.yaml")
            chain = prompt | self.llm.with_structured_output(RouteDecision)
            self.logger.info(f"[{self.name}] LLM chain constructed (prompt → llm → structured output)")
        except Exception as e:
            self.logger.exception(f"[{self.name}] Failed to construct Router chain")
            state.setdefault("errors", []).append(f"[{self.name}] chain init error: {e}")
            return state
        
        user_query = state['user_query']
        df_name = state.get('df_name', '')
        df_desc = state.get('df_desc', '')
        chart_name = state.get('chart_name', '')
        chart_desc = state.get('chart_desc', '')
        previous_node = state.get('previous_node', '_START_')
        input_values = {
            'user_query': user_query, 
            'df_name': df_name, 
            'df_desc': df_desc,
            'chart_name': chart_name,
            'chart_desc': chart_desc,
            'previous_node': previous_node
            }

        self.logger.debug(f"[{self.name}] Input preview: {input_values}")


        try:
            self.logger.info(f"[{self.name}] Invoking LLM for route decision …")
            result: RouteDecision = chain.invoke(input_values)
            self.logger.info(f"[{self.name}] LLM invocation completed")
        except Exception as e:
            self.logger.exception(f"[{self.name}] LLM invocation failed")
            state.setdefault("errors", []).append(f"[{self.name}] llm invoke error: {e}")
            return state
        
        self.logger.info(f"[{self.name}] Decision → action={result.action}")
        self.logger.debug(f"[{self.name}] Reason: {result.reason}")
        if result.notes:
            self.logger.debug(f"[{self.name}] Notes: {result.notes}")

        self.log(message=result.action)
        return {'next_action': result.action, 'previous_node': 'router'}

