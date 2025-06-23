from .base import BaseNode
from .state import ParseState, OCRJsonState
import os

class TableClassificationNode(BaseNode):
    '''
    Parsing된 elements의 table중 OCR할 element 분류
    '''
    def __init__(self, verbose=False, **kwargs):
        super().__init__(verbose=verbose, **kwargs)

    
    def run(self, state: ParseState) -> ParseState:
        return state



class CreateElementsNode(BaseNode):
    '''
    Parsing된 json response를 필요한 elements class에 대입
    '''
    def __init__(self, verbose=False, add_newline=True, **kwargs):
        super().__init__(verbose=verbose, **kwargs)
        self.add_newline = add_newline
        self.newline = "\n" if add_newline else ""
    
    def run(self, state: ParseState) -> ParseState:
        post_processed_elements = []
        directory = os.path.dirname(state["filepath"])
        base_filename = os.path.splitext(os.path.basename(state["filepath"]))[0]


class ElementIntegration(BaseNode):
    '''
    최종적으로 정제시킨 Elements들을 합치는 Node
    '''
    def __init__(self, verbose=False, **kwargs):
        super().__init__(verbose=verbose, **kwargs)

    
    def run(self, state: ParseState) -> ParseState:
        return state


class StructureExtractor(OCRJsonState):
    '''
    LLM을 활용해서 OCR데이터를 구조화시키는 Node
    '''
    def __init__(self, verbose=False, **kwargs):
        super().__init__(verbose=verbose, **kwargs)

    
    def run(self, state: ParseState) -> ParseState:
        return state

    
class ElementsWorkingQueueNode(BaseNode):
    '''
    OCR tool이 필요한 Element를 OCR_json Node로 보내는 Node 

    Element를 반복문을 돌리면서 Queue형태로 OCR_json_tool_Node에 거쳤다가 온 
    Element는 뒤로 다시 보내면서 worflow를 생성하는 Node

    '''
    def __init__(self, verbose=False, **kwargs):
        super().__init__(verbose=verbose, **kwargs)

    
    def run(self, state: ParseState) -> ParseState:
        return state
    

class IntegrateElementNode(BaseNode):
    '''
    구조화된 Element들을 하나의 문서로 만들어서 LLM이 이해할 수 있는 형태로 통합하는 Node
    '''
    def __init__(self, verbose=False, **kwargs):
        super().__init__(verbose=verbose, **kwargs)

    
    def run(self, state: ParseState) -> ParseState:
        return state