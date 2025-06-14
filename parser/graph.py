from .upstage_parser import UpstageOCRNode
from .ocrjsonparser  import GroupXYLine
import os

upstage_ocr_node = UpstageOCRNode(
    api_key=os.environ["UPSTAGE_API_KEY"], verbose=True
)

group_xy_line_node = GroupXYLine(verbose=True)