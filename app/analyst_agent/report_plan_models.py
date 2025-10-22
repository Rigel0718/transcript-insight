from typing import List, Dict, Literal, Optional, Union
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


class AnalysisSpec(BaseModel):
    # 분석 주제
    focus: str = Field(
        default="GPA trend, major GPA",
        description=(
            "이번 분석에서 중점적으로 다룰 초점. 쉼표로 여러 항목을 구분해 입력할 수 있음. "
            "예: 전체 GPA 추이, 전공 과목 성적, 특정 과목군 성취도 등"
        ),
        examples=["GPA trend, major GPA", "core courses performance", "overall GPA improvement"],
    )

    # 독자 맥락
    audience: Literal["student", "evaluator", "advisor"] = Field(
        default="student",
        description="리포트의 주요 대상(학생 본인 / 평가자 / 조언자).",
        examples=["student", "evaluator", "advisor"],
    )
    audience_spec: str = Field(
        default="",
        description=(
            "대상이 평가자/조언자인 경우 구체화(예: AI 기업 채용 담당자, 학과 장학금 심사위원, 멘토 교수). "
            "학생 본인인 경우 비워둘 수 있음."
        ),
        examples=["AI 기업 채용 담당자", "장학금 심사위원", ""],
    )
    audience_goal: str = Field(
        default="general insight",
        description=(
            "대상이 리포트에서 얻고자 하는 목표. "
            "예: 일반적 통찰, 개선 필요 영역 파악, 합격 가능성 평가 등"
        ),
        examples=["general insight", "identify improvement areas", "admission likelihood"],
    )
    evaluation_criteria: str = Field(
        default="",
        description=(
            "참고할 평가 기준을 쉼표로 구분하여 입력. "
            "예: 전공 성취도, 일관성, 도전 과목 이수, 평균 학점 등. 없으면 비워둠."
        ),
        examples=["전공 성취도, 일관성", "도전 과목 이수", ""],
    )
    decision_context: str = Field(
        default="",
        description="이 분석이 사용될 맥락. 예: 채용 전형, 장학금 심사, 진로 상담 등.",
        examples=["채용 전형", "장학금 심사", ""],
    )

    # 분석 범위
    time_scope: str = Field(
        default="전체 학기",
        description="분석 기간 범위. 기본은 전체 학기. 예: 최근 2학기, 3학년, 2022~2024 등.",
        examples=["전체 학기", "최근 2학기", "3학년"],
    )
    comparison_target: Optional[str] = Field(
        default=None,
        description=(
            "비교 기준 또는 대상(옵션). 예: 학과 평균, 지난 학기 본인 성적, 상위 10% 기준 등."
        ),
        examples=["학과 평균", "지난 학기 본인", None],
    )

    # 보고서 톤/스타일
    tone: Literal["neutral", "encouraging", "formal"] = Field(
        default="neutral",
        description="리포트의 문체 톤(중립적 / 격려하는 / 공식적인).",
        examples=["neutral", "encouraging", "formal"],
    )
    language: Literal["ko", "en"] = Field(
        default="ko",
        description="리포트 작성 언어(ko | en).",
        examples=["ko", "en"],
    )
    insight_style: Literal["descriptive", "comparative", "predictive"] = Field(
        default="descriptive",
        description="인사이트 방식: 서술형(descriptive) / 비교형(comparative) / 예측형(predictive).",
        examples=["descriptive", "comparative", "predictive"],
    )
    report_format: Literal["markdown", "html"] = Field(
        default="html",
        description="리포트 산출 포맷. 일반 사용자는 HTML 기본값을 권장.",
        examples=["html", "markdown"],
    )




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