from typing import TypedDict, Annotated, List, Dict, Literal, Optional
import operator

class ReactReportState(TypedDict):

    # User Input
    user_query: Annotated[str, "raw user request for the report"]
    dataset: Annotated[dict, "JSON-like transcript object (already loaded)"]

    # Planner (ReACT -> Thought -> ACT loop)
    task_queue: Annotated[List[dict], "FIFO queue of tasks planned by the agent" , operator.add]
    thoughts: Annotated[List[str], "internal reasoning traces (summarized)" , operator.add]
    actions: Annotated[List[str], "tool names chosen in order", operator.add]
    observations: Annotated[List[str], "key observations from tool outputs", operator.add]

    # Artifacts 
    dataframe_code: Annotated[str, "generated Python code that builds DataFrame from dataset"]
    dataframe: Annotated[Optional[str], "JSON-serialized pandas DataFrame string (small preview)"]
    chart_generation_code: Annotated[str, "generated chart code for current chart task"]
    img_path: Annotated[List[str], "saved chart image paths", operator.add]

    # Runtime execution feedback
    code_output: Annotated[List[str], "stdout captured while running codes", operator.add]
    code_error: Annotated[List[str], "errors/warnings encountered during code execution", operator.add]

    # Reporting
    insights: Annotated[List[str], "analysis paragraphs (Korean)", operator.add]
    report_md: Annotated[str, "final compiled Markdown report"]
    report_path: Annotated[str, "where the markdown is saved"]

    # Control
    next_action: Annotated[str, "routing key decided by controller node"]
    prev_node: Annotated[str, "name of the previous node"]