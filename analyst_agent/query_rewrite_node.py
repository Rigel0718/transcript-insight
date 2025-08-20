from base_node import BaseNode
from analyst_agent.state import ReportState
from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel
from typing import Optional
from langchain.callbacks import get_openai_callback
from .utils import load_prompt_template
from pydantic import BaseModel, Field


class QueryRewrite(BaseModel):
    rewrited_query: str = Field(..., description="Rewritten query")


class QueryRewriteNode(BaseNode):
    def __init__(self, llm: Optional[BaseChatModel] = None, verbose=False, **kwargs):
        super().__init__(verbose=verbose, **kwargs)
        self.llm = llm or self._init_llm()

    def _init_llm(self):
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
        )
        return llm

    def run(self, state: ReportState) -> ReportState:
        prompt = load_prompt_template("prompts/query_rewrite.yaml")
        chain = prompt | self.llm.with_structured_output(QueryRewrite)

        user_query = state['user_query']

        with get_openai_callback() as cb:
            result = chain.invoke({'user_query': user_query})
            cost = cb.total_cost

        state['rewrited_query'] = result.rewrited_query
        state['cost'] = cost

        return state