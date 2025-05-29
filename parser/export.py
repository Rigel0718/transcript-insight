import re
import os
import io
import base64
from PIL import Image
from io import StringIO
import pandas as pd
from .base import BaseNode
from .state import ParseState

class ExportImage(BaseNode):
    def __init__(self, verbose=False, **kwargs):
        """문서에서 추출한 이미지를 PNG 파일로 저장하는 클래스입니다.

        base64로 인코딩된 이미지 데이터를 디코딩하여 PNG 파일로 저장합니다.
        저장된 이미지는 카테고리별로 분류되어 저장됩니다.
        """
        super().__init__(verbose=verbose, **kwargs)

    def save_to_png(self, base64_encoding, dirname, basename, category, index):
        # base64 디코딩
        image_data = base64.b64decode(base64_encoding)

        # 바이트 데이터를 이미지로 변환
        image = Image.open(io.BytesIO(image_data))

        # dirname 내에 images 폴더와 하위 카테고리 폴더 생성
        image_dir = os.path.join(dirname, "images", category)
        os.makedirs(image_dir, exist_ok=True)

        # basename_prefix를 사용하여 이미지 파일명 생성
        base_prefix = os.path.splitext(basename)[0]
        image_filename = (
            f"{base_prefix.upper()}_{category.upper()}_Index_{index}.png"
        )
        image_path = os.path.join(image_dir, image_filename)
        abs_image_path = os.path.abspath(image_path)

        # 이미지 저장
        image.save(abs_image_path)
        return abs_image_path

    def run(self, state: ParseState):
        # 경로
        filepath = state["filepath"]
        dirname = os.path.dirname(filepath)
        basename = os.path.basename(filepath)
        for elem in state["raw_elements"]:
            if elem["category"] in ["figure", "chart", "table"]:
                # base64 인코딩이 있는지 확인
                base64_encoding = elem.get("base64_encoding")
                image_path = self.save_to_png(
                    base64_encoding,
                    dirname,
                    basename,
                    elem["category"],
                    elem["id"],
                )
                # element의 png_filepath key를 만들어서 path저장
                elem["png_filepath"] = image_path

        return {"raw_elements": state["raw_elements"]}
    


class ExportHTML(BaseNode):
    def __init__(self, ignore_new_line_in_text=False, verbose=False, **kwargs):
        """문서 내용을 HTML 형식으로 변환하여 저장하는 클래스입니다.

        이미지가 포함된 경우 base64 인코딩을 통해 HTML 내에 직접 삽입합니다.
        텍스트의 줄바꿈 처리를 선택적으로 할 수 있습니다.
        """
        super().__init__(verbose=verbose, **kwargs)
        self.ignore_new_line_in_text = ignore_new_line_in_text

    def _add_base64_src_to_html(self, html, base64_encoding):
        """HTML 태그에 src 속성을 추가하는 함수"""
        if not base64_encoding:
            return html

        # base64 인코딩된 이미지 데이터를 src에 직접 추가
        pattern = r"<img([^>]*)>"
        replacement = f'<img\\1 src="data:image/png;base64,{base64_encoding}">'
        return re.sub(pattern, replacement, html)

    def run(self, state: ParseState):
        # 원본 파일의 전체 경로를 유지하면서 확장자만 .html로 변경
        filepath = state["filepath"]
        dirname = os.path.dirname(filepath)
        basename = os.path.basename(filepath)
        html_basename = os.path.splitext(basename)[0] + ".html"
        html_filepath = os.path.join(dirname, html_basename)

        # full_markdown 내용을 파일로 저장
        with open(html_filepath, "w", encoding="utf-8") as f:
            for elem in state["elements_from_parser"]:
                # 주석 처리된 요소는 제외
                if elem["category"] in ["header", "footer", "footnote"]:
                    continue

                if elem["category"] in ["figure", "chart", "table"]:
                    # base64 인코딩이 있는지 확인
                    base64_encoding = elem.get("base64_encoding")

                    # HTML에 src 속성 추가
                    modified_html = self._add_base64_src_to_html(
                        elem["content"]["html"], base64_encoding
                    )
                    f.write(modified_html)
                else:
                    if self.ignore_new_line_in_text:
                        f.write(elem["content"]["html"].replace("<br>", " "))
                    else:
                        f.write(elem["content"]["html"])

        self.log(f"HTML file was successfully created: {html_filepath}")

        return {"export": [html_filepath]}