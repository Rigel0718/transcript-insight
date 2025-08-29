from base_node import BaseNode
from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel
from typing import Optional, Dict
from langgraph.types import Command
from langchain.callbacks import get_openai_callback
from .utils import load_prompt_template, to_relative_path
from analyst_agent.report_plan_models import MetricInsight, MetricInsightv2
import pandas as pd

class MetricInsightNode(BaseNode):
    '''
    MetricNode의 결과를 기반으로, 실제 추출된 DF, metric기반으로 분석하는 노드 
    차트도 결국 dataframe으로 분석을 해야하기 multimodal를 사용하지 않는 이상 df로 분석해야하기 때문에 
    이 노드에서 metric결과를 활용해서 LLM을 통해 분석 결과를 생성
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
    
    def run(self, state: Dict) -> Dict:
        prompt = load_prompt_template("prompts/metric_insight_prompt.yaml") 
        # input variable : metric_spec, analysis_spec, dataframe
        chain = prompt | self.llm.with_structured_output(MetricInsight)
        
        metric_spec = state['metric_spec']
        self.logger.info(f"[{self.name}]: {metric_spec}")
        analyst = state['analyst']
        self.logger.info(f"[{self.name}]: {analyst}")
        
        csv_path = state['csv_path']
        relative_csv_path = to_relative_path(csv_path)
        chart_path = state['chart_path']
        relative_chart_path = to_relative_path(chart_path)

        df = pd.read_csv(csv_path)
        dataframe = df.to_dict(orient="records")

        with get_openai_callback() as cb:
            result = chain.invoke(
                input = {
                    'metric_spec':metric_spec,
                    'analysis_spec':analyst, 
                    'dataframe':dataframe,
                    }
                )
            cost = cb.total_cost
        self.logger.info(f"[{self.name}]: {result}")

        metric_insight_v2 = MetricInsightv2(**result.model_dump()).model_copy(update={
        "dataframe": dataframe,
        "csv_path": relative_csv_path,           
        "chart_path": relative_chart_path,       
        })
        return Command(update={'metric_insight': metric_insight_v2, 'cost': cost})