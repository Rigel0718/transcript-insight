
ANALYSIS_SPEC_HELP: dict = {
    "focus": {
        "label": "분석 초점",
        "type": "string(csv)",
        "default": "GPA trend, major GPA",
        "ask": "이번 분석에서 무엇을 강조하고 싶나요? (쉼표로 여러 항목 입력 가능)",
        "help": (
            "리포트가 가장 집중해야 할 포인트를 적습니다. 쉼표로 구분하면 여러 항목을 지정할 수 있습니다.\n"
            "예: 전체 GPA 추이, 전공 과목 성적, 특정 과목군 성취도, 핵심과목 성과, 성적 상승/하락 구간 등."
        ),
        "examples": [
            "GPA trend, major GPA",
            "core courses performance",
            "overall GPA improvement",
            "CS core tracks, semester-wise trend"
        ]
    },

    "audience": {
        "label": "리포트 대상",
        "type": "enum",
        "default": "student",
        "choices": ["student", "evaluator", "advisor"],
        "ask": "리포트를 누구에게 보여줄 예정인가요? (student/evaluator/advisor)",
        "help": (
            "리포트를 읽는 주 대상입니다. student(본인), evaluator(평가자), advisor(멘토/지도) 중에서 선택하세요."
        ),
        "examples": ["student", "evaluator", "advisor"]
    },

    "audience_spec": {
        "label": "대상 구체화",
        "type": "string",
        "default": "",
        "ask": "평가자/조언자라면 구체 대상을 알려주세요. (예: AI 기업 채용 담당자, 학과 장학금 심사위원)",
        "help": (
            "audience가 evaluator/advisor일 때만 구체화합니다. 누가 읽는지 명시하면 리포트의 톤과 구성이 더 정밀해집니다."
        ),
        "examples": ["AI 기업 채용 담당자", "학과 장학금 심사위원", "멘토 교수", ""],
        "when_to_ask": "audience in {'evaluator','advisor'} and not audience_spec"
    },

    "audience_goal": {
        "label": "대상 목표",
        "type": "string",
        "default": "general insight",
        "ask": "대상이 리포트에서 얻고 싶은 것은 무엇인가요?",
        "help": (
            "리포트를 통해 독자가 얻고자 하는 바를 한 문장으로 표현합니다.\n"
            "예: 개선 영역 파악, 합격 가능성 판단, 강점 증거 확보."
        ),
        "examples": ["general insight", "identify improvement areas", "admission likelihood"]
    },

    "evaluation_criteria": {
        "label": "평가 기준",
        "type": "string(csv)",
        "default": "",
        "ask": "참고할 평가 기준이 있나요? (쉼표로 구분, 없으면 비워두세요)",
        "help": (
            "평가자가 중시할 항목을 나열합니다. 예: 전공 성취도, 일관성, 도전 과목 이수, 평균 학점, 상위권 비율 등."
        ),
        "examples": ["전공 성취도, 일관성", "도전 과목 이수", ""]
    },

    "decision_context": {
        "label": "활용 맥락",
        "type": "string",
        "default": "",
        "ask": "이 리포트를 어디에 사용할 예정인가요? (예: 채용 전형, 장학금 심사, 진로 상담)",
        "help": (
            "리포트가 활용될 상황을 명시합니다. 이는 톤, 구성, 주요 지표 선택에 직접적인 영향을 줍니다."
        ),
        "examples": ["채용 전형", "장학금 심사", "진로 상담", ""]
    },

    "time_scope": {
        "label": "분석 기간",
        "type": "string",
        "default": "전체 학기",
        "ask": "분석 기간을 정해주세요. (예: 전체 학기, 최근 2학기, 3학년, 2022~2024)",
        "help": (
            "리포트에서 다룰 기간 범위입니다. 명확히 설정하면 인사이트가 구체화됩니다."
        ),
        "examples": ["전체 학기", "최근 2학기", "3학년", "2022~2024"]
    },

    "comparison_target": {
        "label": "비교 기준",
        "type": "string|null",
        "default": None,
        "ask": "비교 기준이 필요할까요? (예: 학과 평균, 지난 학기 본인, 상위 10%, 없으면 '없음')",
        "help": (
            "비교 기준이 있으면 설득력 있는 리포트를 만들 수 있습니다. 없을 경우 빈칸으로 두세요."
        ),
        "examples": ["학과 평균", "지난 학기 본인", "상위 10%", None]
    },

    "tone": {
        "label": "문체 톤",
        "type": "enum",
        "default": "neutral",
        "choices": ["neutral", "encouraging", "formal"],
        "ask": "문체 톤을 선택하세요. (neutral/encouraging/formal)",
        "help": (
            "neutral(중립적), encouraging(격려형), formal(공식적) 중 하나를 선택합니다."
        ),
        "examples": ["neutral", "encouraging", "formal"]
    },

    "language": {
        "label": "작성 언어",
        "type": "enum",
        "default": "ko",
        "choices": ["ko", "en"],
        "ask": "리포트 언어는 무엇으로 할까요? (ko/en)",
        "help": "리포트가 작성될 언어입니다.",
        "examples": ["ko", "en"]
    },

    "insight_style": {
        "label": "인사이트 방식",
        "type": "enum",
        "default": "descriptive",
        "choices": ["descriptive", "comparative", "predictive"],
        "ask": "인사이트 방식은 어떤 유형이 적합할까요? (descriptive/comparative/predictive)",
        "help": (
            "descriptive(서술형): 현상 설명 중심\n"
            "comparative(비교형): 대상 간 비교 중심\n"
            "predictive(예측형): 경향이나 미래 성과 예측 중심"
        ),
        "examples": ["descriptive", "comparative", "predictive"]
    },

    "report_format": {
        "label": "산출 포맷",
        "type": "enum",
        "default": "html",
        "choices": ["markdown", "html"],
        "ask": "리포트 결과를 어떤 형태로 받고 싶나요? (html/markdown)",
        "help": (
            "일반 사용자에게는 HTML을 추천합니다. 마크다운을 쓰는 워크플로우가 있다면 markdown을 선택하세요."
        ),
        "examples": ["html", "markdown"]
    }
}
