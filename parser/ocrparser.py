from collections import defaultdict
from .state import OCRParseState
from .base import BaseNode
from .utils import load_prompt_template
from .element import TableBoundary
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.language_models.chat_models import BaseChatModel
from typing import Optional
from collections import defaultdict


class GroupXYLine(BaseNode):

    def __init__(self, verbose=False, **kwargs):
        super().__init__(verbose=verbose, **kwargs)


    def run(self, state: OCRParseState):
        '''
        # function 
        - RuleBase로 OCR 좌표를 이용하여 layout을 LLM이 이해할 수 있는 형태로 전처리.

        ## Rule
        OCR 데이터를 열(column) 기준으로 분류하고, 줄 단위로 y값 그룹핑 후
        텍스트는 x 기준 정렬, (text, min_x, min_y) 반환

        ## parameter
        - ocr_data: upstage api를 통해 얻은 json값
        - page_width: 페이지의 폭
        - num_cols: 성적표가 세로로 나누어진 칸 수
        - y_threshold: ocr결과에서 같은 줄이라고 볼 수 있는 y값의 오차범위
        '''
        ocr_data = state['ocr_data']
        page_width = state['page_width']
        num_cols = 3
        y_threshold = 3

        col_width = page_width / num_cols
        columns = defaultdict(list)

        # 열 분류
        for ocr_elem in ocr_data:
            x0 = ocr_elem.vertices['x']
            y0 = ocr_elem.vertices['y']
            col_index = int(x0 // col_width)
            col_index = min(col_index, num_cols - 1)
            columns[col_index].append((y0, x0, ocr_elem.text))

        # 열 순서대로 정렬
        all_texts = []
        for col in range(num_cols):
            sorted_col = sorted(columns[col], key=lambda t: t[0])  # y 기준 정렬
            all_texts.extend(sorted_col)

        # 줄 단위 그룹핑
        lines = []
        current_line = []
        current_y = None

        for y, x, text in all_texts:
            if current_y is None:
                current_y = y
                current_line.append((x, text, y))
            elif abs(y - current_y) <= y_threshold:
                current_line.append((x, text, y))
            else:
                current_line_sorted = sorted(current_line, key=lambda t: t[0])  # x 정렬
                merged_text = " ".join(t[1] for t in current_line_sorted)
                min_x = min(t[0] for t in current_line_sorted)
                min_y = min(t[2] for t in current_line_sorted)
                lines.append((merged_text, min_x, min_y))

                current_line = [(x, text, y)]
                current_y = y

        # 마지막 줄 처리
        if current_line:
            current_line_sorted = sorted(current_line, key=lambda t: t[0])
            merged_text = " ".join(t[1] for t in current_line_sorted)
            min_x = min(t[0] for t in current_line_sorted)
            min_y = min(t[2] for t in current_line_sorted)
            lines.append((merged_text, min_x, min_y))
        return {'grouped_elements' : lines}


class OCRTableBoundaryDetectorNode(BaseNode):

    def __init__(self, verbose=False, llm: Optional[BaseChatModel] = None, **kwargs):
        '''
        ocr 추출된 데이터의 좌표정보와 의미정보를 활용하여,
        table의 boundary를 성적과 관련된 table의 경계부분을 추출하는 node

        output format: 
            {
                "y_top": { y_top },
                "y_bottom": { y_bottom }
            }
        '''
        super().__init__(verbose=verbose, **kwargs)
        self.llm =llm or self._init_llm() 

    def _init_llm(self):
        llm = ChatOpenAI(
        temperature=0, 
        model_name="gpt-4o",  
        )
        return llm

    def run(self, state: OCRParseState):
        
        source=state['ocr_data']

        prompt_template = load_prompt_template('prompts/boundary_detector.yaml')

        parser = PydanticOutputParser(pydantic_object=TableBoundary)
        
        chain = prompt_template | self.llm | parser

        result = chain.invoke({'source' : source})

        return {'grade_table_boundary' : result}
    

class SplitByYBoundaryNode(BaseNode):
    '''
    LLM을 통해 얻은 y boundary 값을 가지고 OCR 값을 분리하는 node
    '''
    def __init__(self, verbose=False, **kwargs):
        super().__init__(verbose=verbose, **kwargs)

    def _split_by_y_bounds(self, lines, y_top, y_bottom):
        # lines [(text, x, y)... ]
        # -3을 하는 이유는 llm이 간혹가다가 의미에 포함되는 것을 경계로 삼아서 정보 손실이 되는 경우가 있기 때문에 
        y_top = y_top-3
        y_bottom = y_bottom-3
        return {
            "top": [r[0] for r in lines if r[2] < y_top],
            "grade": [r[0] for r in lines if y_top <= r[2] < y_bottom], 
            "bottom": [r[0] for r in lines if r[2] >= y_bottom],
        }
    
    def _format_table_sections(self, sections: dict) -> str:
        top_text = "\n".join(sections["top"])
        grade_text = "\n".join(sections["grade"])
        bottom_text = "\n".join(sections["bottom"])

        return (
            "━━━━━━━━━━[Grade Table Head Section]━━━━━━━━━━\n"
            f"{top_text}\n\n"
            "━━━━━━━━━━[Grade Table Main Section]━━━━━━━━━━\n"
            f"{grade_text}\n\n"
            "━━━━━━━━━━[Other Table]━━━━━━━━━━\n"
            f"{bottom_text}"
        )

    def run(self, state: OCRParseState) -> OCRParseState:
        table_boundary : TableBoundary = state['grade_table_boundary']

        lines = state['grouped_elements']
        result = self._split_by_y_bounds(lines, table_boundary.y_top, table_boundary.y_bottom)
        integrated_result = self._format_table_sections(result)
        
        return {'result_element' : integrated_result}