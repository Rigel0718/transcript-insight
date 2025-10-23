from pathlib import Path
from typing import Optional

from app.core import BaseNode
from app.core.util import load_prompt_template
from app.analyst_agent.state import ReportState
from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_community.callbacks.manager import get_openai_callback
from app.analyst_agent.report_plan_models import InformMetric, MetricPlan
from langchain_core.output_parsers import JsonOutputParser

PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"

class DataExtractorNode(BaseNode):
    '''
    transcript 정보를 InformMetric으로 추출
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

    def run(self, state: ReportState) -> ReportState:
        prompt = load_prompt_template(PROMPTS_DIR / "data_extractor_prompt.yaml")
        chain = prompt | self.llm | JsonOutputParser()

        ''' output_schema
        {
            "inform_metric": {
            "name": str,
            "university": str,
            "department": str,
            "admission_date": "YYYY-MM-DD or null",
            "graduation_date": "YYYY-MM-DD or null",
            "degree_number": "str or null",
            "total_credits": float,
            "total_gpa_points": float,
            "overall_gpa": float,
            "overall_percentage": float
            },
            "semantic_course_names": {
            "<metric_id>": ["과목명1", "과목명2", "..."]
            }
        }
        '''
        metric_plan: MetricPlan = state['metric_plan']
        semantic_metrics = []
        for metric_spec in metric_plan:
            if metric_spec.extraction_mode == "semantic":
                semantic_metrics.append({metric_spec.id: metric_spec.extraction_query})
        
        input_values = {
            'dataset': state['dataset'],
            'semantic_metrics': semantic_metrics,
        }

        with get_openai_callback() as cb:
            result = chain.invoke(input_values)
            cost = cb.total_cost

        self.logger.debug("extracted_data=%s", result)
        inform_metric = InformMetric(**result['inform_metric'])
        state['inform_metric'] = inform_metric
        for metric_spec in metric_plan:
            if metric_spec.extraction_mode == "semantic":
                metric_spec.semantic_course_names = result['semantic_course_names'][metric_spec.id]
        state['metric_plan'] = metric_plan
        self.logger.debug("cost=%s", cost)
        state['cost'] = cost

        return state
