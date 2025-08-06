from .base import BaseNode
from .state import Text2ChartState
from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel
from typing import Optional
from .utils import load_prompt_template
from langchain_core.output_parsers import JsonOutputParser

class QueryReWrite(BaseNode):
    '''
    유저의 쿼리를 LLm을 활용하여 Agent가 이해할 수 있게 재 구성해주는 Node.
    '''

    def __init__(self, llm: Optional[BaseChatModel] = None, verbose=False, **kwargs):
        super().__init__(verbose=verbose, **kwargs)
        self.llm = llm or self._init_llm()

    def _init_llm(self):
        llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0,
        )
        return llm 

    def run(self, state: Text2ChartState):
        prompt = load_prompt_template("prompts/query_rewrite.yaml")
        chain = prompt | self.llm | JsonOutputParser()
        input_query = state['query']
        input_dataset = state['dataset']
        input_values = {'query': input_query, 'dataset': input_dataset}
        result = chain.invoke(input_values)
        return {'query': result}

class DataFrameExtractorNode(BaseNode):
    '''
    json(dict) data를 유저의 쿼리 자연어를 참고하여 
    LLM을 활용하여 dataframe으로 추출해주는 코드를 생성해주는 Node.
    '''

    def __init__(self, llm: Optional[BaseChatModel] = None, verbose=False, **kwargs):
        super().__init__(verbose=verbose, **kwargs)
        self.llm = llm or self._init_llm()

    def _init_llm(self):
        llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0,
        )
        return llm 

    def run(self, state: Text2ChartState):
        ...


class Text2ChartNode(BaseNode):
    '''
    재정의된 유저의 쿼리와 추출된 DataFrame으로 시각화 해주는 python code생성
    '''

    def __init__(self, llm: Optional[BaseChatModel] = None, verbose=False, **kwargs):
        super().__init__(verbose=verbose, **kwargs)
        self.llm = llm or self._init_llm()

    def _init_llm(self):
        llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0,
        )
        return llm 

    def run(self, state: Text2ChartState):
        ...