from langgraph.graph import END as LANG_END  # 이름 구분
from langgraph.graph import START as LANG_START
from enum import Enum


class OcrRoute(str, Enum):
    "OCR을 해야하는지 판단하는 edge에 가는 route의 tool name"
    TOOLS = "OCRtools"
    END = LANG_END


class ParserConfig(Enum):
    "sub graph단위의 input, output config 관리"
    START = LANG_START
    END = LANG_END