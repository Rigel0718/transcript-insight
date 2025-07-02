from typing import TypedDict, Annotated, List, Dict, Tuple
import operator
from .element import Element, TableBoundary, OCRElement


class ParseState(TypedDict):
    filepath: Annotated[str, "filepath"]  # 원본 파일 경로

    metadata: Annotated[
        List[Dict], operator.add
    ]  # parsing metadata (api, model, usage)

    elements_from_parser: Annotated[List[Dict], operator.add]  # raw elements from Upstage

    elements: Annotated[List[Element], "elements"]  # Final cleaned elements

    needs_ocr_elements_id : Annotated[List[str], 'needs_ocr_elements', operator.add]


class OCRParseState(TypedDict):
    "OCR로 구조화된 데이터를 추출하는 sub graph의 state"
    
    filepath: Annotated[str, "base_filepath"]

    element_dir : Annotated[str, "element_dir"]

    image_file_path : Annotated[str, "image_file_path"]

    ocr_data: Annotated[List[OCRElement], operator.add]

    page_width: Annotated[int, 'page_width']

    metadata: Annotated[
        List[Dict], operator.add
    ]

    element: Annotated[Element, "originaldocument parsered element"]

    grouped_elements : Annotated[List[Tuple[str, int ,int]], "rulebased_elements"]

    grade_table_boundary: Annotated[TableBoundary, 'output grade_table_boundary']

    result_element : Annotated[str, "result_element"]
    