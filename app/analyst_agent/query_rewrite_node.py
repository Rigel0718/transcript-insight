from pathlib import Path
from typing import Optional

from app.core import BaseNode
from app.core.util import load_prompt_template
from app.analyst_agent.state import ReportState
from langchain.callbacks import get_openai_callback
from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel
from pydantic import BaseModel, Field


PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


class QueryRewrite(BaseModel):
    rewrited_query: str = Field(..., description="Rewritten query")


class QueryRewriteNode(BaseNode):
    '''
    User의 질문이나 요구사항을 LLM이 이해할 수 있도록, 성적표 context에 맞게 변경 또는 재생성하는 노드.
    '''
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
        prompt = load_prompt_template(PROMPTS_DIR / "query_rewrite.yaml")
        chain = prompt | self.llm.with_structured_output(QueryRewrite)

        user_query = state['user_query']

        with get_openai_callback() as cb:
            result = chain.invoke({'user_query': user_query})
            cost = cb.total_cost

        state['rewrited_query'] = result.rewrited_query
        state['cost'] = cost

        return state
