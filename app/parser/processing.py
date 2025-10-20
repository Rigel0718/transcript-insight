from pathlib import Path
from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.output_parsers import JsonOutputParser

from app.core.util import load_prompt_template
from .base import BaseNode
from .state import ParseState
from .element import Element, CheckParsedResult


PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


class TableValidationNode(BaseNode):
    '''
    Parsing된 elements의 table중 OCR할 element 분류
    '''
    def __init__(self, llm: Optional[BaseChatModel] = None, verbose=False, **kwargs):
        super().__init__(verbose=verbose, **kwargs)
        self.llm = llm or self._init_llm()


    def _init_llm(self):
        llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0,
        )
        return llm 
    
    def run(self, state: ParseState) -> ParseState:
        prompt_template = load_prompt_template(PROMPTS_DIR / 'parsed_result_checker_prompt.yaml')

        chain = prompt_template | self.llm.with_structured_output(CheckParsedResult)
        for elem in state['elements']:
            if elem.category == 'table':
                print('table_id  :' ,elem.id)
                source = elem.content
                result : CheckParsedResult = chain.invoke({'source' : source})
                if result.decision == 'YES':
                    elem.ocr_need = True
                    state['needs_ocr_elements_id'] = state['needs_ocr_elements_id'] + [str(elem.id)]
                    print(state['needs_ocr_elements_id'])
            else :
                continue
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




class ElementIntegrationNode(BaseNode):
    '''
    최종적으로 정제시킨 Elements들을 합치는 Node
    '''
    def __init__(self, verbose=False, **kwargs):
        super().__init__(verbose=verbose, **kwargs)

    
    def run(self, state: ParseState) -> ParseState:
        text_blocks = []

        for elem in state['elements']:
            content = (elem.content or "").strip()
            if content:
                text_blocks.append(content)
        result = "\n\n".join(text_blocks)
        return {'transcript_text' : result}
    
class ExtractJsonNode(BaseNode):
    '''
    도출된 transcript text를 json구조형태로 추출하는 Node
    '''
    def __init__(self, llm: Optional[BaseChatModel] = None, verbose=False, **kwargs):
        super().__init__(verbose=verbose, **kwargs)
        self.llm = llm or self._init_llm()
        
    def _init_llm(self):
        llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0,
        )
        return llm 
    
    def run(self, state: ParseState) -> ParseState:
        extract_prompt = load_prompt_template(PROMPTS_DIR / 'extractor_json.yaml')
        chain = extract_prompt | self.llm | JsonOutputParser()

        transcript_text = state['transcript_text']
        result_json = chain.invoke({'transcript_text': transcript_text})
        
        return {'final_result': result_json}
