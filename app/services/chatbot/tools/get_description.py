from dataclasses import dataclass
from langchain.tools import tool, ToolRuntime
from app.services.chatbot.tools.spec_description import ANALYSIS_SPEC_HELP

@dataclass
class Context:
    key: str


@tool("get_spec_description", description="AnalysisSpec의 특정 키에 대한 설명을 가져옵니다.")
def get_spec_description(runtime: ToolRuntime[Context]):
    """
    AnalysisSpec의 특정 키에 대한 설명을 가져옵니다.
    Args:
        key: AnalysisSpec의 키
    Returns:
        AnalysisSpec의 키에 대한 설명 (json)
    """

    key = runtime.context.key

    spec = ANALYSIS_SPEC_HELP.get(key)
    if spec is None:
        raise ValueError(f"Invalid key: {key}")
    return spec


