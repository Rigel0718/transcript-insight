from typing import TypedDict, Annotated, List, Dict
import operator
from analyst_agent.report_plan_models import ReportPlan, ChartSpec, TableSpec, AnalysisSpec, MetricSpec, InformMetric

class ReportState(TypedDict, total=False):
    # user_input
    user_query: Annotated[str, "Original user query or question"] = ''
    dataset: Annotated[str, "Input dataset (as a dictionary or serialized string)"] = ''
    run_id: Annotated[str, "Unique run identifier"] = ''

    # report_element
    report_plan: Annotated[ReportPlan, "Report plan (as a dictionary or serialized string)"] = ''
    metric_plan: Annotated[List[MetricSpec], "List of MetricSpec(id, rationale, compute_hint, chart_type, produces, tags)"] = []
    inform_metric: Annotated[InformMetric, "Normalized student profile & transcript summary (name, university, department, dates, credits, GPA, percentage)"] = ''
    chart: Annotated[ChartSpec, "generated chart spec(name, chart_type, df_ref, options)"] = ''
    table: Annotated[TableSpec, "generated table spec(name, desc, query, constraints)"] = ''
    analyst: Annotated[AnalysisSpec, "Config for Analysis spec (focus, audience, tone, language)"] = ''

    rewrite_query: Annotated[str, "Rewritten query"] = ''

    cost: Annotated[float, "total cost(dollars)"] = 0.0
    
    