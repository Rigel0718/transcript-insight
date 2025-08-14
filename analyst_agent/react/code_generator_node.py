from analyst_agent.react.base import BaseNode
from analyst_agent.react.state import ChartState, DataFrameState
from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel
from typing import Optional
from .utils import load_prompt_template
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser

class DataFrameCodeGeneratorNode(BaseNode):
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

    def run(self, state: DataFrameState) -> DataFrameState:
        prompt = load_prompt_template("prompts/generate_dataframe_code.yaml")
        chain = prompt | self.llm | JsonOutputParser()
        input_query = state['user_query']
        self.log(message=input_query)
        print(state.keys())
        input_values = {'user_query': input_query, 'dataset': state['dataset'], 'error_log': state['error_log']}
        result = chain.invoke(input_values)
        state['df_code'] = result['df_code']
        state['df_info'] = result['df_info']
        self.log(message=str(result['df_info']))
        return state


class ChartCodeGeneratorNode(BaseNode):
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

    def run(self, state: ChartState) -> ChartState:
        prompt = load_prompt_template("prompts/generate_chart_code.yaml")
        chain = prompt | self.llm | JsonOutputParser()
        input_query = state['user_query']
        input_dataframe = state['dataframe']
        code_error = state['error_logs']
        input_values = {'user_query': input_query, 'dataframe': input_dataframe, 'error_log': code_error}
        chart_generation_code = chain.invoke(input_values)
        ''' output foramt (json)
        {{
          "code": """차트 생성 Python 코드""",
          "chart_name": "차트 제목 (영어)",
          "img_path": "{{artifact_dir}}/{{chart_name}}"  # 예: ./artifacts/sales_by_month.png
          "chart_desc": "차트 목적, 차트 설명 (한글).. etc"
        }}
        '''
        chart_info = (chart_generation_code['chart_name'], chart_generation_code['chart_desc'])
        if chart_generation_code['code'] == "None":
            state['previous_node'] = 'text2chart'
        else :
            state['previous_node'] = 'code_executor'
        state['chart_code'] = chart_generation_code['code']
        state['img_path'] = chart_generation_code['img_path']
        state['chart_info'] = chart_info
        return state