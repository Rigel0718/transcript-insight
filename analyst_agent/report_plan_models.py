from typing import List, Dict, Literal, Optional
from pydantic import BaseModel, Field, conlist

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


# class AnalysisSpec(BaseModel):
#     focus: List[str]  # ["GPA_trend","at_risk_courses","major_vs_overall"]
#     audience: Literal["student","evaluator","advisor"] = "student"
#     audience_spec: str = ""  # ex) "AI company recruiter", "scholarship committee", "promotion reviewer"
#     audience_goal: str = "general insight"  # ex) "general insight", "risk screening", "promotion review"
#     tone: Literal["neutral","encouraging","formal"] = "neutral"
#     language: Literal["ko","en"] = "ko"

class AnalysisSpec(BaseModel):
    # 분석 주제
    focus: List[str]  
    
    # 독자 맥락
    audience: Literal["student","evaluator","advisor"] = "student"
    audience_spec: str = ""  
    audience_goal: str = "general insight"
    audience_values: List[str] = []          # ex) ["성실성","논리적 사고"]
    evaluation_criteria: List[str] = []      # ex) ["전공 성취도", "일관성"]
    decision_context: str = "채용 선발"      # ex) "채용 선발", "장학금 심사"
    
    # 분석 범위
    time_scope: str = "전체 학기"
    comparison_target: Optional[str] = None
    priority_focus: List[str] = []           # 분석 중 가장 강조할 포인트
    
    # 보고서 톤/스타일
    tone: Literal["neutral","encouraging","formal"] = "neutral"
    language: Literal["ko","en"] = "ko"
    detail_level: Literal["summary","balanced","in_depth"] = "balanced"
    insight_style: Literal["descriptive","comparative","predictive"] = "descriptive"
    evidence_emphasis: Literal["low","medium","high"] = "medium"
    tone_variation: Optional[str] = None
    
    # 산출물 구성
    output_format: List[Literal["text","chart","table","recommendation"]] = ["text"]
    include_recommendations: bool = False
    highlight_style: Literal["numbers","growth","risk","strengths"] = "growth"




class MetricSpec(BaseModel):
    id: str = Field(..., description="Stable identifier like 'gpa_trend'")
    rationale: str
    compute_hint: str = Field(..., description="Short hint for DF/Chart generation")
    chart_type: Optional[Literal["line","bar","stacked_bar","scatter","pie","none"]] = "none"
    produces: Literal["table","chart","metric"] = Field(default_factory="metric")
    tags: List[str] = Field(default_factory=list)
    extraction_mode: Literal["rule","semantic"] = "semantic"
    extraction_query: Optional[str] = None
    semantic_course_names: Optional[List[str]] = None
    # # 선택: 가중치/우선순위, 오버라이드 등도 포함 가능
    # priority: Optional[float] = Field(default=None, description="Higher = earlier scheduling")
    # overrides: Optional[dict] = None

class MetricPlan(BaseModel):
    # 최소 3개, 최대 6개
    metrics: conlist(MetricSpec, min_length=1, max_length=4)


class InformMetric(BaseModel):
    name: str
    university: str
    department: str
    admission_date: str
    graduation_date: Optional[str] = None
    degree_number: Optional[str] = None
    total_credits: float
    total_gpa_points: float
    overall_gpa: float
    overall_percentage: float


class KeyNumber(BaseModel):
    label: str
    value: float | int | str
    unit: Optional[str] = None


class MetricInsight(BaseModel):
    metric_id: str
    title: str = Field(..., description="짧은 소제목 (e.g., '수학 역량 요약')")
    insight: str = Field(..., description="2 - 5줄 요약. 사실 중심, 과장 금지")
    produces: Literal["table","chart","metric"] = Field(default_factory="metric")
    key_numbers: List[KeyNumber] = Field(default_factory=list)
    caveats: List[str] = Field(default_factory=list)

class MetricInsightv2(MetricInsight):
    dataframe: Optional[List[Dict]] = None
    csv_path: Optional[str] = ''
    chart_path: Optional[str] = ''

class ReportPlan(BaseModel):
    metric_insights: List[MetricInsightv2]