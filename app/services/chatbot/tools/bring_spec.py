from langchain.tools import tool, ToolRuntime
from app.services.chatbot.spec_store import spec_store
from app.services.chatbot.chatbot_node import UserContext



@tool
def bring_current_spec(runtime: ToolRuntime[UserContext]) -> dict:
    """
    현재 AnalysisSpec을 가져옵니다.
    """
    session_id = runtime.context.session_id

    return spec_store.get_spec(session_id)

