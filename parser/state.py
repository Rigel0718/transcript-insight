from typing import TypedDict, Annotated, List, Dict
import operator
from .element import Element
from langchain_core.documents import Document


class ParseState(TypedDict):
    filepath: Annotated[str, "filepath"]  # 원본 파일 경로

    metadata: Annotated[
        List[Dict], operator.add
    ]  # parsing metadata (api, model, usage)

    raw_elements: Annotated[List[Dict], operator.add]  # raw elements from Upstage

    elements: Annotated[List[Element], "elements"]  # Final cleaned elements

    unstructured_elements: Annotated[str, 'unstrutured_element']


class OCRJsonState(TypedDict):
    "OCR로 Jsondata를 추출하는 sub graph의 state"
    
    filepath: Annotated[str, "filepath"]

    ocr_data: Annotated[List[Dict], operator.add]

    page_width: Annotated[int, 'page_width']

    extracted_json: Annotated[List[Dict], 'output jsondata']
    