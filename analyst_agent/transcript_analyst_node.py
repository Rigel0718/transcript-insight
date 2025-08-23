from base_node import BaseNode
from analyst_agent.state import ReportState
from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel
from typing import Optional, List
from langchain.callbacks import get_openai_callback
from .utils import load_prompt_template
from langchain_core.output_parsers import StrOutputParser
from analyst_agent.report_plan_models import AnalysisSpec, TableSpec, ChartSpec, ReportPlan


class TranscriptAnalystNode(BaseNode):
    def __init__(self, llm: Optional[BaseChatModel] = None, verbose=False, **kwargs):
        super().__init__(verbose=verbose, **kwargs)
        self.llm = llm or self._init_llm()

    def _init_llm(self):
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
        )
        return llm
        
    def run(self, state: ReportState) -> ReportState:
        prompt = load_prompt_template("prompts/transcript_analyst.yaml")
        chain = prompt | self.llm | StrOutputParser()

        query = state['rewrited_query']
        report_plan: ReportPlan = state['report_plan']
        analyst: AnalysisSpec = report_plan.analysis
        tables: List[TableSpec] = report_plan.tables
        charts: List[ChartSpec] = report_plan.charts

        focus = analyst.focus
        audience = analyst.audience
        audience_spec = analyst.audience_spec
        tone = analyst.tone
        language = analyst.language

        for table in tables:
            dict_table = {
                'table_name': table.name,
                'table_desc': table.desc,
            }

        for chart in charts:
            dict_chart = {
                'chart_name': chart.name,
                'chart_type': chart.chart_type,
                'df_ref': chart.df_ref,
            }

        input_values = {
            'user_query': query, 
            'focus': focus, 
            'audience': audience,
            'audience_spec': audience_spec,
            'tone': tone, 
            'language': language,
            'tables': dict_table,
            'charts': dict_chart,
            }

        with get_openai_callback() as cb:
            result = chain.invoke(input_values)
            cost = cb.total_cost

        state['cost'] = cost
        state['report_plan'] = ReportPlan(**result)
        return state