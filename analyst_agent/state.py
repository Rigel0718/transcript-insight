from typing import TypedDict, Annotated, List, Dict
import operator


class Text2ChartState(TypedDict):
    user_query: Annotated[str, "user_query"]

    code: Annotated[str, ""]

    code_error: Annotated[str, ""]

    img_path: Annotated[str, ""]

    img_bytes: Annotated[str, ""]

    chart_desc: Annotated[str, ""]

    prev_node: Annotated[str, ""]