from .upstage_parser import UpstageOCRNode, UpstageParseNode
from .ocrparser  import GroupXYLine, OCRTableBoundaryDetectorNode, SplitByYBoundaryNode
from .processing import CreateElementsNode, TableValidationNode, ElementIntegrationNode
from .state import OCRParseState, ParseState
from .route import need_ocr_tool
from .base import BaseNode
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph
import os
from langgraph.checkpoint.memory import MemorySaver
import uuid
from langchain_core.runnables import RunnableConfig  

# TODO ocr_json_graph -> chain form으로 만들어서 tool처럼 사용할 수 있도록 구현하기.
def ocr_grade_extractor_graph() -> CompiledStateGraph:
    upstage_ocr_node = UpstageOCRNode(
        api_key=os.environ["UPSTAGE_API_KEY"], verbose=True
    )

    group_xy_line_node = GroupXYLine(verbose=True)

    ocr_extract_boundary_node = OCRTableBoundaryDetectorNode(verbose=True)
    
    grade_table_integrated_node = SplitByYBoundaryNode(verbose=True)

    ocr_json_workflow = StateGraph(OCRParseState)

    ocr_json_workflow.add_node('upstage_ocr_parser', upstage_ocr_node)
    ocr_json_workflow.add_node('group_by_xy', group_xy_line_node)
    ocr_json_workflow.add_node('extract_boundary_agent', ocr_extract_boundary_node)
    ocr_json_workflow.add_node('grade_table_integrated_node', grade_table_integrated_node)

    ocr_json_workflow.add_edge('upstage_ocr_parser', 'group_by_xy')
    ocr_json_workflow.add_edge('group_by_xy', 'extract_boundary_agent')
    ocr_json_workflow.add_edge('extract_boundary_agent','grade_table_integrated_node')

    ocr_json_workflow.set_entry_point('upstage_ocr_parser')
    ocr_json_workflow.set_finish_point('grade_table_integrated_node')
    
    return ocr_json_workflow.compile()



class OCRSubGraphNode(BaseNode):
    '''
    element에서 ocrparser가 필요하다면 ocr_subgraph를 실행시키는 node
    '''
    def __init__(self, verbose=False, **kwargs):
        super().__init__(verbose=verbose, **kwargs)

    def run(self, state: ParseState):
        
        random_id = str(uuid.uuid4())

        config = RunnableConfig(recursion_limit=5, configurable={"thread_id": '1'}) 
        self.log(f'OCRSubGraphNode START')
        for elem in state['elements']:
            if elem.ocr_need :
                self.log(f"START OCR sub graph element table number {elem.id}")
                ocr_graph = ocr_grade_extractor_graph()
                result : OCRParseState = ocr_graph.invoke(
                    input=
                        {
                        'element' : elem, 
                        'grade_image_filepath': state['filepath'], 
                        'element_id' : elem.id, 
                        'base64_encoding': elem.base64_encoding
                        },
                    config=config
                    )
                elem.content = result['result_element']
        self.log(f'OCRSubGraphNode END')
        return {"elements": state["elements"]}



def transcript_extract_graph() ->CompiledStateGraph:
    upstage_document_parse_node = UpstageParseNode(
        api_key=os.environ["UPSTAGE_API_KEY"], verbose=True
    )
    preprocessing_elements_node = CreateElementsNode(verbose=True)

    table_elements_validation_node = TableValidationNode(verbose=True)

    ocr_subgraph_node = OCRSubGraphNode(verbose=True)

    integrate_elements_node = ElementIntegrationNode(verbose=True)
    
    upstage_document_parser_workflow = StateGraph(ParseState)

    upstage_document_parser_workflow.add_node('upstage_document_parse_node', upstage_document_parse_node)
    upstage_document_parser_workflow.add_node('preprocessing_elements_node', preprocessing_elements_node)
    upstage_document_parser_workflow.add_node('table_elements_validation_node', table_elements_validation_node)
    upstage_document_parser_workflow.add_node('ocr_subgraph_node', ocr_subgraph_node)
    upstage_document_parser_workflow.add_node('integrate_elements_node', integrate_elements_node)

    upstage_document_parser_workflow.add_edge('upstage_document_parse_node', 'preprocessing_elements_node')
    upstage_document_parser_workflow.add_edge('preprocessing_elements_node','table_elements_validation_node')
    upstage_document_parser_workflow.add_conditional_edges(
        'table_elements_validation_node',
        need_ocr_tool,
        {False: 'integrate_elements_node', True: 'ocr_subgraph_node'}
    )
    upstage_document_parser_workflow.add_edge('ocr_subgraph_node','integrate_elements_node')

    upstage_document_parser_workflow.set_entry_point('upstage_document_parse_node')
    upstage_document_parser_workflow.set_finish_point('integrate_elements_node')
    
    return upstage_document_parser_workflow.compile(checkpointer=MemorySaver())