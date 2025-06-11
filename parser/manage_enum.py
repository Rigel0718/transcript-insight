from langgraph.graph import END as LANG_END  # 이름 구분
from enum import Enum


class Route(str, Enum):
    TOOLS = "tools"
    END = LANG_END
