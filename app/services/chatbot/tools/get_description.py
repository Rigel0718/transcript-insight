from app.services.chatbot.tools.spec_description import ANALYSIS_SPEC_HELP
from pydantic import BaseModel, Field
from langchain.tools import tool

class AnalysisSpecInput(BaseModel):
    key: str = Field(description="AnalysisSpec's key")

@tool("get_spec_description",args_schema=AnalysisSpecInput ,description="AnalysisSpec의 특정 키에 대한 설명을 가져옵니다.")
def get_spec_description(key: str) -> dict:
    """
    AnalysisSpec의 특정 키에 대한 설명을 가져옵니다.
    Args:
        key: AnalysisSpec의 키
    Returns:
        AnalysisSpec의 키에 대한 설명 (json)
    """


    spec = ANALYSIS_SPEC_HELP.get(key)
    if spec is None:
        raise ValueError(f"Invalid key: {key}")
    return spec


