from .base import BaseNode
from .state import ParseState, OCRJsonState
from .element import Element
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
    pydantic basemodel를 활용해서 검증.
    '''
    def __init__(self, verbose=False, add_newline=True, **kwargs):
        super().__init__(verbose=verbose, **kwargs)
        self.add_newline = add_newline
        self.newline = "\n" if add_newline else ""
    
    def run(self, state: ParseState) -> ParseState:
        post_processed_elements = []

        for element in state["elements_from_parser"]:
            elem = None

            # 'footnote', 'header', 'footer'는 활용 X 
            if element['category'] in ['footnote', 'header', 'footer']:
                continue
        
            # table category가 핵심 내용
            if element['category'] in ['table']:

                elem = Element(
                    category=element['category'],
                    content=element['content']['markdown'] + self.newline,
                    base64_encoding=element['base64_encoding'],
                    id=element['id'],
                    coordinates=element['coordinates'],
                )

            elif element['category'] in ['heading1']:
        
                    elem = Element(
                        category=element['category'],
                        content=f'# {element["content"]["text"]}{self.newline}',
                        markdown=element['content']['markdown'],
                        id=element['id'],
                    )

            elif element['category'] in ["caption", 'paragraph', 'list', 'index']:

                elem = Element(
                    category=element['category'],
                    content=element['content']['text'] + self.newline,
                    markdown=element['content']['markdown'],
                    id=element['id'],
                    )

            if elem is not None:
                post_processed_elements.append(elem)


            return {"elements": post_processed_elements}



class CreateOCRElementNode(OCRJsonState):
    '''
    OCRParser 정보를 OCRElement로 검증
    OCRElement: pydantic basemodel 
    '''
    def __init__(self, verbose=False, **kwargs):
        super().__init__(verbose=verbose, **kwargs)

    
    def run(self, state: OCRJsonState) -> OCRJsonState:
        post_processed_elements = []

        for element in state['raw_elements']:
            elem = None

            
        return state



class ElementIntegrationNode(BaseNode):
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
    
class SplitByYBoundaryNode(BaseNode):
    '''
    LLM을 통해 얻은 y boundary 값을 가지고 OCR 값을 분리하는 node
    '''
    def __init__(self, verbose=False, **kwargs):
        super().__init__(verbose=verbose, **kwargs)

    
    def run(self, state: ParseState) -> ParseState:
        return state