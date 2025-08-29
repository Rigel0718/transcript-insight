from typing import TypedDict, Annotated, List
from analyst_agent.report_plan_models import AnalysisSpec, MetricSpec, InformMetric, ReportPlan

class ReportState(TypedDict, total=False):
    # user_input
    user_query: Annotated[str, "Original user query or question"] = ''
    dataset: Annotated[str, "Input dataset (as a dictionary or serialized string)"] = ''
    run_id: Annotated[str, "Unique run identifier"] = ''

    # report_element
    report_plan: Annotated[ReportPlan, "List of MetricInsight"] = []
    metric_plan: Annotated[List[MetricSpec], "List of MetricSpec(id, rationale, compute_hint, chart_type, produces, tags)"] = []
    inform_metric: Annotated[InformMetric, "Normalized student profile & transcript summary (name, university, department, dates, credits, GPA, percentage)"] = ''
    analyst: Annotated[AnalysisSpec, "Config for Analysis spec (focus, audience, tone, language)"] = ''

    rewrite_query: Annotated[str, "Rewritten query"] = ''

    cost: Annotated[float, "total cost(dollars)"] = 0.0
    
    