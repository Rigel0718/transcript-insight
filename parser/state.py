from typing import TypedDict, Annotated, List, Dict, Tuple
import operator
from .element import Element, TableBoundary, OCRElement


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

    element_dir : Annotated[str, "element_dir"]

    image_file_path : Annotated[str, "image_file_path"]

    ocr_data: Annotated[List[OCRElement], operator.add]

    page_width: Annotated[int, 'page_width']

    element: Annotated[Element, "document parsered element"]

    grouped_elements : Annotated[List[Tuple[str, int ,int]], "elements"]

    grade_table_boundary: Annotated[TableBoundary, 'output grade_table_boundary']

    result_element : Annotated[str, "result_element"]
    