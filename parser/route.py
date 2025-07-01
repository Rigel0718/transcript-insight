from .state import ParseState

def need_ocr_tool(state: ParseState):
    if state["unstructured_elements"] == "<<Emty>>":
        return False
    else:
        return True
    
def route_table(state: ParseState) -> str:
    if len(state.get("needs_ocr_elements", [])) > 0:
        return "ocr_parsing_node"
    return "next_node"