from .base import BaseNode
from .state import ParseState
import os

class TableClassificationNode(BaseNode):
    '''
    Parsing된 elements의 table중 OCR할 element 분류
    '''
    ...



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
    ...