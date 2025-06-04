import requests
import json
import os
import time
from .base import BaseNode
from .state import ParseState



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

        parsed_document_json_file_path = self._parse_document_via_upstage(filepath)

        with open(parsed_document_json_file_path, 'r') as f:
            data = json.load(f)

        metadata = {
            'api' : data.pop('api'),
            'model' : data.pop('model'),
            'usage' : data.pop('usage'),
        }

        duration = time.time() - start_time
        self.log(f"Finished Parsing in {duration:.2f} seconds")

        return {"metadata": [metadata], "raw_elements": [data["elements"]]}


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

    def _document_ocr_via_upstage(self, input_file_path : str):
        url = "https://api.upstage.ai/v1/document-digitization"
        headers = {"Authorization": f"Bearer {self.api_key}"}

        files = {"document": open(input_file_path, "rb")}
        data = {"model": 'ocr'}
        response = requests.post(url, headers=headers, files=files, data=data)

        if response.status_code == 200:
            # 분석 결과를 저장할 JSON 파일 경로 생성
            output_file_path = os.path.splitext(input_file_path)[0]+ '_ocr_' + ".json"

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

        parsed_document_json_file_path = self._document_ocr_via_upstage(filepath)

        with open(parsed_document_json_file_path, 'r') as f:
            data = json.load(f)

        metadata = {
            'api' : data.pop('api'),
            'model' : data.pop('model'),
            'usage' : data.pop('usage'),
        }

        duration = time.time() - start_time
        self.log(f"Finished Parsing in {duration:.2f} seconds")

        return {"metadata": [metadata], "raw_elements": [data["elements"]]}
