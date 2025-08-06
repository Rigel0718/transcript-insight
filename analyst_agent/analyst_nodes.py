from pydantic import Json
from .base import BaseNode
from .state import Text2ChartState
from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel
from typing import Optional
from .utils import load_prompt_template
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
import io
import matplotlib.pyplot as plt
from contextlib import redirect_stdout
import traceback

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
        chain = prompt | self.llm | StrOutputParser()
        input_query = state['query']
        input_dataset = state['dataset']
        input_values = {'query': input_query, 'dataset': input_dataset}
        result = chain.invoke(input_values)
        return {'query': result, 'prev_node': 'START'}

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
        prompt = load_prompt_template("prompts/generate_dataframe_code.yaml")
        chain = prompt | self.llm | StrOutputParser()
        input_query = state['rewrite_query']
        input_dataset = state['dataset']
        input_values = {'user_query': input_query, 'dataset': input_dataset}
        dataframe_extract_code = chain.invoke(input_values)
        return {'dataframe_code': dataframe_extract_code, 'prev_node': 'query_rewrite'}


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
        prompt = load_prompt_template("prompts/generate_chart_code.yaml")
        chain = prompt | self.llm | JsonOutputParser()
        input_query = state['rewrite_query']
        input_dataframe = state['dataframe']
        input_values = {'user_query': input_query, 'dataframe': input_dataframe}
        chart_generation_code = chain.invoke(input_values)
        ''' output foramt (json)
        {{
          "code": """차트 생성 Python 코드""",
          "img_path": "./output/chart.png"
        }}
        '''
        if chart_generation_code['code'] == "None":
            state['prev_node'] = 'text2chart'
        else :
            state['prev_node'] = 'code_executor'
        return {'chart_generation_code': chart_generation_code['code'], 'img_path': chart_generation_code['img_path']}


class CodeExecutorNode(BaseNode):
    '''
    생성된 python code를 실행하고 결과를 반환하는 Node.
    '''
    def __init__(self, verbose=False, **kwargs):
        super().__init__(verbose=verbose, **kwargs)

    def run(self, state: Text2ChartState):
        code = state['chart_generation_code']
        output_stream = io.StringIO()
        plt.clf()

        with redirect_stdout(output_stream):
            try:
                exec(code, globals())
                return {
                    "code_output": output_stream.getvalue(),
                    "code_error": None,
                    "prev_node": 'text2chart'
                }
            except Exception as e:
                error_trace = traceback.format_exc()
                return {
                    "code_output": output_stream.getvalue(),
                    "code_error": f"{str(e)}\n{error_trace}",
                    "prev_node": 'text2chart'
                }