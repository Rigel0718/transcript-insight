from app.base_node.base import BaseNode
from app.analyst_agent.react_code_agent.state import ChartState, DataFrameState, Status
from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_community.callbacks.manager import get_openai_callback
from typing import Optional
from .utils import load_prompt_template
import pandas as pd
from pydantic import BaseModel, Field
import os


class DataFrameSpec(BaseModel):
    df_code: str = Field(..., description="Python code to generate the DataFrame")
    df_name: str = Field(..., description="DataFrame name")
    df_desc: str = Field(..., description="DataFrame description")


class ChartSpec(BaseModel):
    chart_code: str = Field(..., description="Python code to generate the chart")
    chart_name: str = Field(..., description="Chart title")
    chart_desc: str = Field(..., description="Chart purpose/description in Korean")

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
            model="gpt-4.1-mini",
            temperature=0,
        )
        return llm 

    def run(self, state: DataFrameState) -> DataFrameState:
        try:
            prompt = load_prompt_template("prompts/generate_dataframe_code.yaml")
            chain = prompt | self.llm.with_structured_output(DataFrameSpec)
            self.logger.info("LLM chain constructed (prompt → llm → JSON parser)")
        except Exception as e:
            self.logger.exception("Failed to construct LLM chain")
            state.setdefault("errors", []).append(f"[DataFrameCodeGeneratorNode] chain init error: {e}")
            return state

        input_query = state.get("user_query", "")
        dataset = state.get("dataset", {})
        error_log = state.get("error_log", "")
        previous_df_code = state.get("df_code", "")
        input_values = {'user_query': input_query, 'dataset': dataset, 'error_log': error_log, 'previous_df_code': previous_df_code}

        self.logger.debug(f"error_log: {error_log}")
        self.logger.debug(f"chain input preview: {input_values}")
        
        inc_cost = 0.0
        try:
            self.logger.info("Invoking LLM for df_code/df_info …")
            with get_openai_callback() as cb:
                result = chain.invoke(input_values)
            inc_cost = getattr(cb, "total_cost", 0.0)
            self.logger.info("LLM invocation done")
        except Exception as e:
            status = Status(status="alert", message=f"LLM invocation failed: {e}")
            self.logger.exception("LLM invocation failed")
            state.setdefault("errors", []).append(f"[{self.name}] llm invoke error: {e}")
            state['status'] = status
        finally:
            state['cost'] = state.get('cost', 0.0) + float(inc_cost)

        df_code = result.df_code
        df_name = result.df_name
        df_desc = result.df_desc

        if not df_code:
            self.logger.warning("LLM returned empty df_code")
        if not df_name:
            self.logger.warning("LLM returned empty df_name")
        if not df_desc:
            self.logger.warning("LLM returned empty df_desc")

        state['df_code'] = df_code
        state['df_name'] = df_name
        state['df_desc'] = df_desc

        self.logger.info(f"df_code: {df_code}")
        self.logger.info(f"df_name: {df_name}")
        self.logger.info(f"df_desc: {df_desc}")
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
            model="gpt-4.1-mini",
            temperature=0,
        )
        return llm 

    def run(self, state: ChartState) -> ChartState:

        try:
            prompt = load_prompt_template("prompts/generate_chart_code.yaml")
            chain = prompt | self.llm.with_structured_output(ChartSpec)
            self.logger.info("LLM chain constructed (prompt → llm → JSON parser)")
        except Exception as e:
            self.logger.exception("Failed to construct LLM chain")
            state.setdefault("errors", []).append(f"[{self.name}] chain init error: {e}")
            return state
        
        input_query = state.get("user_query", "")
        df_name = state.get("df_name")
        df_desc = state.get("df_desc")
        csv_path = state.get("csv_path")
        df_code = state.get("df_code")           
        code_error = state.get("error_log", "")
        df_meta = state.get("df_meta", {})

        self.logger.info("user_query received")
        self.logger.debug(f"user_query: {input_query}")
        if df_name is None:
            self.logger.warning("df_name is missing (expected df_name)")
        else:
            self.logger.debug(f"df_name: {df_name}")

        if df_desc is None:
            self.logger.warning("df_desc is missing (expected df_desc)")
        else:
            self.logger.debug(f"df_desc: {df_desc}")

        if csv_path is None:
            self.logger.warning("csv_path is missing (expected csv_path)")
        else:
            self.logger.debug(f"csv_path: {csv_path}")

        if df_code is None:
            self.logger.warning("df_code is missing (columns/dtypes expected)")
        else:
            self.logger.debug(f"df_code preview: {df_code}")

        if code_error:
            self.logger.debug(f"previous error_logs: {code_error}")

        
        csv_path = state.get("csv_path")
        if not csv_path or not os.path.isfile(csv_path):
            msg = f"CSV not ready or missing: {csv_path}, Must going to 'to_gen_df'"
            self.logger.warning(msg)
            state.setdefault("errors", []).append(f"[{self.name}] {msg}")
            state["status"] = Status(status="alert", message=msg)
            return state

        # CSV 파일 읽기
        df = pd.read_csv(csv_path)

        # DataFrame을 dict로 변환
        data_dict = df.to_dict(orient="records")

        input_values = {
            'user_query': input_query,
            'df_name': df_name,
            'df_desc': df_desc,
            'csv_path': csv_path,
            'dataframe_dict': data_dict,
            'df_code': df_code,
            'error_log': code_error,
            'df_meta': df_meta
        }
        
        inc_cost = 0.0
        try:
            self.logger.info("Invoking LLM for chart code/info …")
            with get_openai_callback() as cb:
                chart_generator_result = chain.invoke(input_values)
            inc_cost = getattr(cb, "total_cost", 0.0)
            self.logger.info("LLM invocation done")
        except Exception as e:
            status = Status(status="alert", message=f"LLM invocation failed: {e}")
            self.logger.exception("LLM invocation failed")
            state.setdefault("errors", []).append(f"[{self.name}] llm invoke error: {e}")
            state['status'] = status
        finally:
            state['cost'] = state.get('cost', 0.0) + float(inc_cost)
        
        ''' output foramt (pydantic model: ChartSpec)
          "chart_code": """차트 생성 Python 코드""",
          "chart_name": "차트 제목 (영어)",
          "chart_desc": "차트 목적, 차트 설명 (한글).. etc"
        '''
        chart_code = chart_generator_result.chart_code
        chart_name = chart_generator_result.chart_name
        chart_desc = chart_generator_result.chart_desc

        if not chart_code:
            self.logger.warning("LLM returned empty chart code")
        if not chart_name:
            self.logger.warning("LLM returned empty chart_name")
        if not chart_desc:
            self.logger.warning("LLM returned empty chart_desc")
    
        

        if not chart_code or str(chart_code).strip().lower() == "none":
            state["previous_node"] = "chart_code_generator"
            self.logger.info("No chart code returned → route to 'chart_code_generator'")
        else:
            state["previous_node"] = "code_executor"
            self.logger.info("Chart code returned → route to 'code_executor'")

        state['chart_code'] = chart_code
        state['chart_name'] = chart_name
        state['chart_desc'] = chart_desc

        self.logger.info(f"chart_code: {chart_code}")
        self.logger.info(f"chart_name='{chart_name}'")
        self.logger.info(f"chart_desc='{chart_desc}'")
        self.logger.debug("Chart CodeGen end")
        return state