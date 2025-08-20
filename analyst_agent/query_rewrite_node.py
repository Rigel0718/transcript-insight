from base_node import BaseNode
from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel
from typing import Optional

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

    def run(self, state: dict) -> dict:
        return state