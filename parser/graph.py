from .upstage_parser import UpstageOCRNode
from .ocrjsonparser  import GroupXYLine, OCRJsonExtractorNode
from .state import OCRJsonState
from langgraph.graph import StateGraph
import os

upstage_ocr_node = UpstageOCRNode(
    api_key=os.environ["UPSTAGE_API_KEY"], verbose=True
)

group_xy_line_node = GroupXYLine(verbose=True)

ocr_extract_json_node = OCRJsonExtractorNode(verbose=True)

ocr_json_workflow = StateGraph(OCRJsonState)

ocr_json_workflow.add_node('upstage_ocr_parser', upstage_ocr_node)
ocr_json_workflow.add_node('group_by_xy', group_xy_line_node)
ocr_json_workflow.add_node('ocr_extract_llm', ocr_extract_json_node)