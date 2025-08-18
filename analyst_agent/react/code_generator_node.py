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
        try:
            prompt = load_prompt_template("prompts/generate_dataframe_code.yaml")
            chain = prompt | self.llm | JsonOutputParser()
            self.logger.info("LLM chain constructed (prompt → llm → JSON parser)")
        except Exception as e:
            self.logger.exception("Failed to construct LLM chain")
            state.setdefault("errors", []).append(f"[DataFrameCodeGeneratorNode] chain init error: {e}")
            return state

        input_query = state.get("user_query", "")
        dataset = state.get("dataset", {})
        error_log = state.get("error_log", "")
        input_values = {'user_query': input_query, 'dataset': dataset, 'error_log': error_log}

        self.logger.debug(f"chain input preview: {input_values}")
        
        try:
            self.logger.info("Invoking LLM for df_code/df_info …")
            result = chain.invoke(input_values)
            self.logger.info("LLM invocation done")
            self.logger.debug(f"raw LLM result: {result}")
        except Exception as e:
            self.logger.exception("LLM invocation failed")
            state.setdefault("errors", []).append(f"[{self.name}] llm invoke error: {e}")
            return state

        df_code = result.get("df_code")
        df_info = result.get("df_info")

        if not df_code:
            self.logger.warning("LLM returned empty df_code")
        if not df_info:
            self.logger.warning("LLM returned empty df_info")

        state['df_code'] = df_code
        state['df_info'] = df_info

        self.logger.info(f"df_code: {df_code}")
        self.logger.info(f"df_info: {df_info}")
        self.logger.debug("DF CodeGen end")
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

        try:
            prompt = load_prompt_template("prompts/generate_chart_code.yaml")
            chain = prompt | self.llm | JsonOutputParser()
            self.logger.info("LLM chain constructed (prompt → llm → JSON parser)")
        except Exception as e:
            self.logger.exception("Failed to construct LLM chain")
            state.setdefault("errors", []).append(f"[{self.name}] chain init error: {e}")
            return state
        
        input_query = state.get("user_query", "")
        df_info = state.get("df_info")            
        df_code = state.get("df_code")           
        code_error = state.get("error_logs", "")

        self.logger.info("user_query received")
        self.logger.debug(f"user_query: {input_query}")
        if df_info is None:
            self.logger.warning("df_info is missing (expected (df_name, df_desc))")
        else:
            self.logger.debug(f"df_info: {df_info}")

        if df_code is None:
            self.logger.warning("df_code is missing (columns/dtypes metadata expected)")
        else:
            self.logger.debug(f"df_code preview: {df_code}")

        if code_error:
            self.logger.debug(f"previous error_logs: {code_error}")


        input_values = {'user_query': input_query, 'df_info': df_info, 'df_code': df_code, 'error_log': code_error}
        
        try:
            self.logger.info("Invoking LLM for chart code/info …")
            chart_generation_code = chain.invoke(input_values)
            self.logger.info("LLM invocation done")
            self.logger.debug(f"raw LLM result: {chart_generation_code}")
        except Exception as e:
            self.logger.exception("LLM invocation failed")
            state.setdefault("errors", []).append(f"[{self.name}] llm invoke error: {e}")
            return state
        
        ''' output foramt (json)
        {{
          "code": """차트 생성 Python 코드""",
          "chart_name": "차트 제목 (영어)",
          "img_path": "{{artifact_dir}}/{{chart_name}}"  # 예: ./artifacts/sales_by_month.png
          "chart_desc": "차트 목적, 차트 설명 (한글).. etc"
        }}
        '''
        code = chart_generation_code.get("code")
        chart_name = chart_generation_code.get("chart_name")
        img_path = chart_generation_code.get("img_path")
        chart_desc = chart_generation_code.get("chart_desc")

        if not code:
            self.logger.warning("LLM returned empty chart code")
        if not chart_name:
            self.logger.warning("LLM returned empty chart_name")
        if not img_path:
            self.logger.warning("LLM returned empty img_path (template expects '{{artifact_dir}}/{{chart_name}}.png')")
        if not chart_desc:
            self.logger.warning("LLM returned empty chart_desc")
    
        
        chart_info = (chart_name, chart_desc)

        if not code or str(code).strip().lower() == "none":
            state["previous_node"] = "chart_code_generator"
            self.logger.info("No chart code returned → route to 'chart_code_generator'")
        else:
            state["previous_node"] = "code_executor"
            self.logger.info("Chart code returned → route to 'code_executor'")

        state['chart_code'] = code
        state['img_path'] = img_path
        state['chart_info'] = chart_info

        self.logger.info(f"chart_code: {code}")
        self.logger.info(f"chart_name='{chart_name}', img_path='{img_path}'")
        self.logger.debug("Chart CodeGen end")
        return state