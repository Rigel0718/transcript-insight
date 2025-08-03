from .base import BaseNode
from .state import Text2ChartState



class DataFrameExtractorNode(BaseNode):
    '''
    json(dict) data를 유저의 쿼리 자연어를 참고하여 
    LLM을 활용하여 dataframe으로 추출해주는 코드를 생성해주는 Node.
    '''

    def __init__(self, verbose=False, **kwargs):
        super().__init__(verbose=verbose, **kwargs)


    def run(self, state: Text2ChartState):
        ...