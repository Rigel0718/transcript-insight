from pathlib import Path
from typing import Optional

from app.core import BaseNode
from app.core.util import load_prompt_template
from app.analyst_agent.state import ReportState
from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_community.callbacks.manager import get_openai_callback
from app.analyst_agent.report_plan_models import MetricPlan, MetricSpec


PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


gpa_trend_metric = MetricSpec(
    id="gpa_trend",
    rationale="Term별 GPA 변화 추세를 요약.",
    compute_hint="compute term_gpa by term (if missing, derive from course grades & credits); line chart term vs term_gpa; include table of term, term_gpa;",
    chart_type="line",
    produces="chart",
    tags=["required","trend","gpa","term"],
    extraction_mode="rule",
    extraction_query=None
)

credit_category_share_metric = MetricSpec(
    id="credit_category_share",
    rationale="이수 학점의 카테고리별 구성 비중을 요약.",
    compute_hint=(
        "aggregate total_credits by course_category (or course_type|is_core|department); "
        "compute percentage of total; pie chart category vs credit_share; include table; "
        "category labels must be written in Korean. (e.g., '전공선택(D)' instead of just 'D')"
    ),
    chart_type="pie",
    produces="chart",
    tags=["required","composition","credits","category","share"],
    extraction_mode="rule",
    extraction_query=None
)


class AnalysisPlannerNode(BaseNode):
    '''
    성적표 분석 보고서를 작성하기 위한 플래너 노드.
    AnalysisSpec을 참고하여 필요한 Metric을 계획
    '''
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
        prompt = load_prompt_template(PROMPTS_DIR / "analysis_planner_prompt.yaml")
        chain = prompt | self.llm.with_structured_output(MetricPlan)
        
        analyst = state['analyst']
        self.logger.info(f"[{self.name}]: {analyst}")

        with get_openai_callback() as cb:
            result = chain.invoke(input = {'analysis_spec':analyst})
            cost = cb.total_cost
        self.logger.info(f"[{self.name}]: {result}")
        default_metrics = [gpa_trend_metric, credit_category_share_metric]
        state['metric_plan'] = default_metrics + result.metrics
        self.logger.info(f'COST : {cost}')
        state['cost'] = cost
        return state
