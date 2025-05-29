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