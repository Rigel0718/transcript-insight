from .base import BaseNode
from .state import ParseState, OCRParseState
from .element import Element ,CheckParsedResult
from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser, PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from typing import Optional
from .utils import get_chat_prompt_yaml

class TableClassificationNode(BaseNode):
    '''
    Parsing된 elements의 table중 OCR할 element 분류
    '''
    def __init__(self, llm: Optional[BaseChatModel] = None, verbose=False, **kwargs):
        super().__init__(verbose=verbose, **kwargs)
        self.llm = llm or self._init_llm(llm)


    def _init_llm(self):
        llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0,
        )
        return llm 
    
    def run(self, state: ParseState) -> ParseState:
        template = get_chat_prompt_yaml('prompt/parsed_result_checker_prompt.yaml')
        prompt_template = PromptTemplate(
            template=template,
            input_variables=['source']
        )
        parser = PydanticOutputParser(pydantic_object=CheckParsedResult)
        
        chain = prompt_template | self.llm | parser

        for elem in state['elements']:
            if elem['category'] == 'table':
                source = elem['content']
                result = chain.invoke({'source' : source})
                if result == 'YES':
                    state['needs_ocr_elements'] + elem
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



class CreateOCRElementNode(OCRParseState):
    '''
    OCRParser 정보를 OCRElement로 검증
    OCRElement: pydantic basemodel 
    '''
    def __init__(self, verbose=False, **kwargs):
        super().__init__(verbose=verbose, **kwargs)

    
    def run(self, state: OCRParseState) -> OCRParseState:
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


class StructureExtractor(OCRParseState):
    '''
    LLM을 활용해서 OCR데이터를 구조화시키는 Node
    '''
    def __init__(self, verbose=False, **kwargs):
        super().__init__(verbose=verbose, **kwargs)

    
    def run(self, state: OCRParseState) -> OCRParseState:
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
    