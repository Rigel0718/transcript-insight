from .upstage_parser import UpstageOCRNode, UpstageParseNode
from .ocrparser  import GroupXYLine, OCRTableBoundaryDetectorNode
from .processing import CreateElementsNode, TableValidationNode, ElementIntegrationNode, ElementsWorkingQueueNode
from .state import OCRParseState, ParseState
from .route import need_ocr_tool
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph
import os
from langgraph.checkpoint.memory import MemorySaver

# TODO ocr_json_graph -> chain form으로 만들어서 tool처럼 사용할 수 있도록 구현하기.
def ocr_grade_extractor_graph() -> CompiledStateGraph:
    upstage_ocr_node = UpstageOCRNode(
        api_key=os.environ["UPSTAGE_API_KEY"], verbose=True
    )

    group_xy_line_node = GroupXYLine(verbose=True)

    ocr_extract_boundary_node = OCRTableBoundaryDetectorNode(verbose=True)

    ocr_json_workflow = StateGraph(OCRParseState)

    ocr_json_workflow.add_node('upstage_ocr_parser', upstage_ocr_node)
    ocr_json_workflow.add_node('group_by_xy', group_xy_line_node)
    ocr_json_workflow.add_node('extract_boundary_agent', ocr_extract_boundary_node)

    ocr_json_workflow.add_edge('upstage_ocr_parser', 'group_by_xy')
    ocr_json_workflow.add_edge('group_by_xy', 'extract_boundary_agent')

    ocr_json_workflow.set_entry_point('upstage_ocr_parser')
    ocr_json_workflow.set_finish_point('extract_boundary_agent')
    
    return ocr_json_workflow.compile(checkpointer=MemorySaver())

def transcript_extract_graph() ->CompiledStateGraph:
    upstage_document_parse_node = UpstageParseNode(
        api_key=os.environ["UPSTAGE_API_KEY"], verbose=True
    )
    preprocessing_elements_node = CreateElementsNode(verbose=True)

    grader_table_elements_node = TableValidationNode(verbose=True)

    elements_working_queue_node = ElementsWorkingQueueNode(verbose=True)

    ocr_json_tool_node = ocr_grade_extractor_graph()

    integrate_elements_node = ElementIntegrationNode(verbose=True)
    
    upstage_document_parser_workflow = StateGraph(ParseState)

    upstage_document_parser_workflow.add_node('upstage_document_parse_node', upstage_document_parse_node)
    upstage_document_parser_workflow.add_node('preprocessing_elements_node', preprocessing_elements_node)
    upstage_document_parser_workflow.add_node('grader_table_elements_node', grader_table_elements_node)
    upstage_document_parser_workflow.add_node('ocr_json_tool_node', ocr_json_tool_node)
    upstage_document_parser_workflow.add_node('integrate_elements_node', integrate_elements_node)
    upstage_document_parser_workflow.add_node('elements_working_queue_node', elements_working_queue_node)

    upstage_document_parser_workflow.add_edge('upstage_document_parse_node', 'preprocessing_elements_node')
    upstage_document_parser_workflow.add_edge('preprocessing_elements_node','grader_table_elements_node')
    upstage_document_parser_workflow.add_edge('grader_table_elements_node', 'elements_working_queue_node')
    upstage_document_parser_workflow.add_conditional_edges(
        'elements_working_queue_node',
        need_ocr_tool,
        {False: 'integrate_elements_node', True: 'ocr_json_tool_node'}
    )
    upstage_document_parser_workflow.add_edge('ocr_json_tool_node','elements_working_queue_node')

    upstage_document_parser_workflow.set_entry_point('upstage_document_parse_node')
    upstage_document_parser_workflow.set_finish_point('integrate_elements_node')
    
    return upstage_document_parser_workflow.compile(checkpointer=MemorySaver())