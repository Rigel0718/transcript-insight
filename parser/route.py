from .state import ParseState
    
def need_ocr_tool(state: ParseState) -> str:
    if len(state.get("needs_ocr_elements_id", [])) > 0:
        return True
    return False