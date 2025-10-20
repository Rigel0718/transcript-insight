from pathlib import Path
from typing import Optional

from app.core import BaseNode
from app.core.util import load_prompt_template
from app.application.chatbot.state import ChatbotState
from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseChatModel
from langchain_community.callbacks.manager import get_openai_callback


PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


class ChatbotNode(BaseNode):
    def __init__(self, llm: Optional[BaseChatModel] = None, verbose=False, **kwargs):
        super().__init__(verbose=verbose, **kwargs)
        self.llm = llm or self._init_llm()

    def _init_llm(self):
        llm = ChatOpenAI(
            model="gpt-4.1-mini",
            temperature=0.7,
        )
        return llm

    def run(self, state: ChatbotState) -> ChatbotState:
        prompt = load_prompt_template(PROMPTS_DIR / "chatbot_prompt.yaml")
        chain = prompt | self.llm
        with get_openai_callback() as cb:
            result = chain.invoke(state)
            cost = cb.total_cost
        return {"messages": [result], "cost": cost}
