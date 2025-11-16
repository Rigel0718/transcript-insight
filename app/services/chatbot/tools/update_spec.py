from app.services.chatbot.spec_store import spec_store
from langchain.tools import tool
from app.services.chatbot.chatbot_node import UserContext
from langchain.tools import ToolRuntime

@tool
def update_spec(runtime: ToolRuntime[UserContext], update: dict) -> dict:
    """
    Update parts of the AnalysisSpec (partial update).
    """
    session_id = runtime.context.session_id
    current = spec_store.get_spec(session_id)
    new_spec = {**current, **update}
    spec_store.set_spec(session_id, new_spec)
    return new_spec