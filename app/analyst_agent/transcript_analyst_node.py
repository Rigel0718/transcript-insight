from app.base_node import BaseNode
from app.analyst_agent.state import ReportState
from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel
from typing import Optional, List
from langchain_community.callbacks.manager import get_openai_callback
from .utils import load_prompt_template
from langchain_core.output_parsers import StrOutputParser
from app.analyst_agent.report_plan_models import AnalysisSpec, MetricInsightv2, InformMetric, MetricSpec, ReportPlan

class TranscriptAnalystNode(BaseNode):
    def __init__(self, llm: Optional[BaseChatModel] = None, verbose=False, **kwargs):
        super().__init__(verbose=verbose, **kwargs)
        self.llm = llm or self._init_llm()

    def _init_llm(self):
        llm = ChatOpenAI(
            model="gpt-4.1-mini",
            temperature=0.4,
        )
        return llm
        
    def run(self, state: ReportState) -> ReportState:
        prompt = load_prompt_template("prompts/transcript_analyst_prompt.yaml")
        chain = prompt | self.llm | StrOutputParser()

        analyst: AnalysisSpec = state['analyst']
        report_plan: ReportPlan = state['report_plan']
        inform_metric: InformMetric = state['inform_metric']

        input_values = {
            'analysis_spec': analyst,
            'metric_insights': report_plan,
            'inform_metric': inform_metric,
            'report_title':'',
            'report_date':state['run_id'],
            }

        with get_openai_callback() as cb:
            result = chain.invoke(input_values)
            cost = cb.total_cost
        self.logger.info(f"[{self.name}]: {result}")
        self.logger.info(f'COST : {cost}')
        state['cost'] = cost
        state['report'] = result
        return state