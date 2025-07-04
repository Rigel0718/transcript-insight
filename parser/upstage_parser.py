import requests
import json
import os
import time
import re
import base64
import io
from PIL import Image
from .base import BaseNode
from .state import ParseState, OCRParseState
from .element import OCRElement



DEFAULT_CONFIG = {
    "ocr": "auto",    # "auto" | "force"
    "coordinates": True, # true | false
    "output_formats": "['html', 'text', 'markdown']", # default ['html]
    "model": "document-parse",
    "base64_encoding": "['figure', 'chart', 'table']", # default []
}


class UpstageParseNode(BaseNode):
    def __init__(self, api_key, verbose=False, **kwargs):
        """
        DocumentParse 클래스의 생성자

        :param api_key: Upstage API 인증을 위한 API 키
        :param config: API 요청에 사용할 설정값. None인 경우 기본 설정 사용
        """
        super().__init__(verbose=verbose, **kwargs)
        self.api_key = api_key
        self.config = DEFAULT_CONFIG

    def _parse_document_via_upstage(self, input_file_path : str):
        """
        Upstage의 Document Parse API를 호출하여 문서 분석을 수행합니다.

        :param input_file: 분석할 PDF 파일의 경로
        :return: 분석 결과가 저장된 JSON 파일의 경로
        """

        # API request header
        headers = {'Authorization' : f'Bearer {self.api_key}'}

        # post API requests
        with open(input_file_path, 'rb') as f:
            files = {"document": f}
            response = requests.post(
                "https://api.upstage.ai/v1/document-digitization",
                headers=headers,
                data=self.config,
                files=files
            )
        

        # API 응답 처리 및 결과 저장
        if response.status_code == 200:
            # 분석 결과를 저장할 JSON 파일 경로 생성
            output_file_path = os.path.splitext(input_file_path)[0] + ".json"

            # 분석 결과를 JSON 파일로 저장
            with open(output_file_path, "w") as f:
                json.dump(response.json(), f, ensure_ascii=False, indent=2)

            return output_file_path
        else:
            # API 요청이 실패한 경우 예외 발생
            raise ValueError(f"Unexpected status code: {response.status_code}")
    
    def run(self, state: ParseState):
        """
        주어진 입력 파일에 대해 문서 분석을 실행합니다.

        :param input_file: 분석할 PDF 파일의 경로
        :return: 분석 결과가 저장된 JSON 파일의 경로
        """
    
        start_time = time.time()
        filepath = state['filepath']
        self.log(f"Start Parsing: {filepath}")

        # parsed_document_json_file_path = self._parse_document_via_upstage(filepath)
        parsed_document_json_file_path = '../example_data/test_example/grade.json'

        with open(parsed_document_json_file_path, 'r') as f:
            data = json.load(f)

        metadata = {
            'api' : data.pop('api'),
            'model' : data.pop('model'),
            'usage' : data.pop('usage'),
        }

        duration = time.time() - start_time
        self.log(f"Finished Parsing in {duration:.2f} seconds")

        return {"metadata": [metadata], "elements_from_parser": data["elements"], "original_document_parser_filepath": parsed_document_json_file_path}


#TODO Upstage OCR 기능 추가하기. -> 위에 Document Parsing과 OCR 기능을 상속 받을 수 있는 기초 클래스를 생성도 추가.


class UpstageOCRNode(BaseNode):
    def __init__(self, api_key, verbose=False, **kwargs):
        """
        DocumentParse 클래스의 생성자

        :param api_key: Upstage API 인증을 위한 API 키
        :param config: API 요청에 사용할 설정값. None인 경우 기본 설정 사용
        """
        super().__init__(verbose=verbose, **kwargs)
        self.api_key = api_key

    def _document_ocr_via_upstage(self, input_file_path,  dirname, index):
        url = "https://api.upstage.ai/v1/document-digitization"
        headers = {"Authorization": f"Bearer {self.api_key}"}

        files = {"document": open(input_file_path, "rb")}
        data = {"model": 'ocr'}
        response = requests.post(url, headers=headers, files=files, data=data)

        ocr_filename = (
            f"grade_element_{index}_ocr_.json"
        )
        ocr_file_path = os.path.join(dirname, ocr_filename)

        if response.status_code == 200:
            # 분석 결과를 저장할 JSON 파일 경로 생성

            # 분석 결과를 JSON 파일로 저장
            with open(ocr_file_path, "w") as f:
                json.dump(response.json(), f, ensure_ascii=False, indent=2)

            return ocr_file_path
        else:
            # API 요청이 실패한 경우 예외 발생
            raise ValueError(f"Unexpected status code: {response.status_code}")
    
    def _metadata_ocr_json(self, data):
        #단일 페이지라고 가정
        metadata = dict()
        # data['pages'][0]['words'][0]['boundingBox']['vertices'][0]  => x,y 좌측 상단 좌표
        # data['metadata']['pages'][0] =>  metadata {height, width, page} 
        metadata['model']=data['modelVersion']
        data['metadata']['pages'][0].pop('page') # metadata에서 height, width값만 
        metadata['size']=data['metadata']['pages'][0]
        metadata['text']=data['text']
        return metadata

    def _cleaning_text(self, text):
        '''
        OCR 과정에서 나오는 오류 해결
        '''
        text = re.sub(r'\b([A-D])O\b', r'\g<1>0', text) #'AO' → 'A0'
        text = text.replace('|', 'I') # '|' → 'I'
        return text

    def _save_to_png(self, base64_encoding, dirname, index):
        # base64 디코딩
        image_data = base64.b64decode(base64_encoding)

        # 바이트 데이터를 이미지로 변환
        image = Image.open(io.BytesIO(image_data))

        # basename_prefix를 사용하여 이미지 파일명 생성
        image_filename = (
            f"grade_element_{index}.png"
        )
        image_path = os.path.join(dirname, image_filename)
        abs_image_path = os.path.abspath(image_path)

        # 이미지 저장
        image.save(abs_image_path)
        return abs_image_path
    

    def run(self, state: OCRParseState):
        """
        주어진 입력 파일에 대해 문서 분석을 실행합니다.

        :param input_file: 분석할 PDF 파일의 경로
        :return: 분석 결과가 저장된 JSON 파일의 경로
        """
    
        start_time = time.time()
        filepath = state['grade_image_filepath']
        basedir = os.path.dirname(filepath)
        element_dir = os.path.join(basedir, f"element_{state['element_id']}")
        os.makedirs(element_dir, exist_ok=True)
        state['element_dir'] = element_dir

        self.log(f"Start Parsing: {element_dir}")
        image_file_path = self._save_to_png(state['base64_encoding'], element_dir, state['element_id'])
        ocr_json_file_path = self._document_ocr_via_upstage(image_file_path, element_dir, state['element_id'])
        state['image_file_path'] = image_file_path

        with open(ocr_json_file_path, 'r') as f:
            data = json.load(f)

        metadata = self._metadata_ocr_json(data)

        update_words = []
        for word in data['pages'][0]['words']:
            confidence = word.get('confidence', '0')
            if float(confidence) <= 0.6:
                continue
            elem = None
            elem = OCRElement(
                id=word['id'],
                vertices=word['boundingBox']['vertices'][0], # 좌측상단 좌표만 추출
                text=self._cleaning_text(word['text'])
            )
            
            update_words.append(elem)

        duration = time.time() - start_time
        self.log(f"Finished Parsing in {duration:.2f} seconds")

        return {'metadata': [metadata], 'ocr_data': update_words, 'page_width': metadata['size']['width'], 'ocr_json_file_path' : ocr_json_file_path}
