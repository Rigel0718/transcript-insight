from typing import List, Dict, Literal, Optional
from pydantic import BaseModel, Field


class TableSpec(BaseModel):
    name: str
    desc: str
    query: str  # DF를 만들기 위한 사용자 의도(리라이트 결과)
    constraints: Dict = Field(default_factory=dict)

class ChartSpec(BaseModel):
    name: str
    chart_type: Literal["line","bar","scatter","pie","hist","box"]
    df_ref: str  # 어떤 표로부터 만드는지 (name)
    options: Dict = Field(default_factory=dict)  # aggregation, hue, facet, etc..


class AnalysisSpec(BaseModel):
    focus: List[str]  # ["GPA_trend","at_risk_courses","major_vs_overall"]
    audience: Literal["student","parent","advisor"] = "student"
    tone: Literal["neutral","encouraging","formal"] = "neutral"
    language: Literal["ko","en"] = "ko"


class ReportPlan(BaseModel):
    tables: List[TableSpec]
    charts: List[ChartSpec]
    analysis: AnalysisSpec
    output_format: Literal["md","html","pdf"] = "md"
    title: str = "성적표 분석 보고서"