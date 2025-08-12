from typing import TypedDict, Annotated, List, Dict, Literal, Optional
import operator

class ReactReportState(TypedDict):

    # User Input
    user_query: Annotated[str, "raw user request for the report"]
    dataset: Annotated[Dict, "JSON-like transcript object (already loaded)"]

    # Planner (ReACT -> Thought -> ACT loop)
    task_queue: Annotated[List[Dict], "FIFO queue of tasks planned by the agent" , operator.add]
    thoughts: Annotated[List[str], "internal reasoning traces (summarized)" , operator.add]
    actions: Annotated[List[str], "tool names chosen in order", operator.add]
    observations: Annotated[List[str], "key observations from tool outputs", operator.add]

    # Artifacts 
    dataframe_code: Annotated[str, "generated Python code that builds DataFrame from dataset"]
    dataframe: Annotated[Optional[str], "JSON-serialized pandas DataFrame string (small preview)"]
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


class AgentContextState(TypedDict):
    # Input / Environment
    user_query: Annotated[str, "Original request or question from the user"]
    dataset: Annotated[Dict | str, "Input dataset (as a dictionary or serialized string)"]
    artifact_dir: Annotated[str, "Directory path for storing generated artifacts (CSV, images, etc.)"]
    work_dir: Annotated[str, "Working directory path for temporary or intermediate files"]
    allow_scan_df: Annotated[bool, "Whether scanning/previewing the entire DataFrame is allowed"]

    # Progress Tracking
    phase: Annotated[Literal["planning", "executing", "reporting"], "Current processing phase of the agent"]
    attempts: Annotated[Dict, "Number of attempts per task type, e.g., {'df': int, 'chart': int}"]
    
    generated_codes: Annotated[List[str], "generated Python code that builds DataFrame from dataset", operator.add]

    # DataFrame Information
    df_handle: Annotated[List[str], "Reference or identifier of the loaded DataFrame", operator.add]
    df_meta: Annotated[List[Dict], "Metadata about the DataFrame (columns, dtypes, shape, etc.)", operator.add]
    csv_path: Annotated[List[str], "File paths to generated CSV files", operator.add]

    # Chart Information
    image_paths: Annotated[List[str], "File paths to generated chart images", operator.add]

    # Execution Logs / Errors
    last_stdout: Annotated[str, "Captured standard output from the last execution"]
    last_stderr: Annotated[str, "Captured standard error from the last execution"]
    last_error: Annotated[str, "Summary or message of the last error encountered"]
    errors: Annotated[List[str], "List of all error messages encountered during the process"]

class DataFrameState(TypedDict, total=False):
    # Code / Input
    df_code: Annotated[str, "Python code that generates a DataFrame from the dataset"]
    # Results / Artifacts
    df_handle: Annotated[List[str], "List of registered DataFrame names"]
    df_meta: Annotated[List[Dict], "Metadata for each DataFrame (schema/shape/columns, etc.)", operator.add]
    csv_path: Annotated[List[str], "List of saved CSV file paths", operator.add]
    # Execution logs / Errors
    stdout: Annotated[str, "Standard output from the last DataFrame execution"]
    stderr: Annotated[str, "Standard error output from the last DataFrame execution"]
    attempts: Annotated[int, "Number of attempts to execute the DataFrame code"]
    last_error: Annotated[str, "Error message from the last DataFrame execution"]
    errors: Annotated[List[str], "List of all error messages encountered during the process"]