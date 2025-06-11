from langgraph.graph import END as LANG_END  # 이름 구분
from enum import Enum


class OcrRoute(str, Enum):
    "OCR을 해야하는지 판단하는 edge에 가는 route의 tool name"
    TOOLS = "OCRtools"
    END = LANG_END
