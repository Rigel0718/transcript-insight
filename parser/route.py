from .state import ParseState

def need_ocr_tool(state: ParseState):
    if state["unstructured_elements"] == "<<Emty>>":
        return False
    else:
        return True