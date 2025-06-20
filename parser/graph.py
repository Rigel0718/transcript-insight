from .upstage_parser import UpstageOCRNode, UpstageParseNode
from .ocrjsonparser  import GroupXYLine, OCRJsonExtractorNode
from .processing import CreateElementsNode, TableClassificationNode
from .state import OCRJsonState, ParseState
from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph
import os

# TODO ocr_json_graph -> chain form으로 만들어서 tool처럼 사용할 수 있도록 구현하기.
def ocr_json_graph() -> CompiledStateGraph:
    upstage_ocr_node = UpstageOCRNode(
        api_key=os.environ["UPSTAGE_API_KEY"], verbose=True
    )

    group_xy_line_node = GroupXYLine(verbose=True)

    ocr_extract_json_node = OCRJsonExtractorNode(verbose=True)

    ocr_json_workflow = StateGraph(OCRJsonState)

    ocr_json_workflow.add_node('upstage_ocr_parser', upstage_ocr_node)
    ocr_json_workflow.add_node('group_by_xy', group_xy_line_node)
    ocr_json_workflow.add_node('ocr_extract_llm', ocr_extract_json_node)

    ocr_json_workflow.add_edge('upstage_ocr_parser', 'group_by_xy')
    ocr_json_workflow.add_edge('group_by_xy', 'ocr_extract_llm')
    ocr_json_workflow.add_edge('ocr_extract_llm', END)

    ocr_json_workflow.set_entry_point('upstage_ocr_parser')
    
    return ocr_json_workflow.compile()

def transcript_extract_graph():
    upstage_document_parse_node = UpstageParseNode(
        api_key=os.environ["UPSTAGE_API_KEY"], verbose=True
    )
    preprocessing_elements_node = CreateElementsNode(verbose=True)

    grader_table_elements_node = TableClassificationNode(verbose=True)

    elements_working_queue_node = ...

    ocr_json_tool_node = ocr_json_graph()

    integrate_elements_node = ...
    
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

    ...