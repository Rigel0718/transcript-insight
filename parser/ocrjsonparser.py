from collections import defaultdict
from state import OCRJsonState
from .base import BaseNode

class GroupXYLine(BaseNode):

    def __init__(self, verbose=False, **kwargs):
        super().__init__(verbose=verbose, **kwargs)


    def run(state: OCRJsonState):
        '''
        ## function ##
        성적표 document 특징상 신문처럼 칸마다 세로로 layout되어있기 때문에 
        세로로 cols 값 대로 나누고, 한 줄 씩 묶어주는 함수

        ## parameter ##
        ocr_data: upstage api를 통해 얻은 json값
        page_width: 페이지의 폭
        num_cols: 성적표가 세로로 나누어진 칸 수
        y_threshold: ocr결과에서 같은 줄이라고 볼 수 있는 y값의 오차범위
        '''
        ocr_data = state['ocr_data']
        page_width = state['page_width']
        num_cols = 3
        y_threshold = 3

        col_width = page_width / num_cols
        columns = defaultdict(list)

        # 열 분류
        for entry in ocr_data:
            x0 = entry["boundingBox"]["vertices"][0]["x"]
            y0 = entry["boundingBox"]["vertices"][0]["y"]
            col_index = int(x0 // col_width)
            col_index = min(col_index, num_cols - 1)
            columns[col_index].append((y0, x0, entry["text"]))

        # 좌 -> 우, 각 열 내부 y 정렬
        all_texts = []
        for col in range(num_cols):
            sorted_col = sorted(columns[col], key=lambda t: t[0])  # y 기준 정렬
            all_texts.extend(sorted_col)

        # y가 비슷한 것들끼리 묶기 + 같은 줄 내 x 기준 정렬
        lines = []
        current_line = []
        current_y = None

        for y, x, text in all_texts:
            if current_y is None:
                current_y = y
                current_line.append((x, text))
            elif abs(y - current_y) <= y_threshold:
                current_line.append((x, text))
            else:
                # x 기준 정렬
                current_line_sorted = [t[1] for t in sorted(current_line, key=lambda t: t[0])]
                lines.append(current_line_sorted)

                current_line = [(x, text)]
                current_y = y

        if current_line:
            current_line_sorted = [t[1] for t in sorted(current_line, key=lambda t: t[0])]
            lines.append(current_line_sorted)

        return lines
