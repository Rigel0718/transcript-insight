from typing import TypedDict, Annotated, List, Dict, Tuple
import operator


class DataFrameState(TypedDict, total=False):
    # Code / Input
    user_query: Annotated[str, "Original user query or question"] = ''
    dataset: Annotated[str, "Input dataset (as a dictionary or serialized string)"] = ''
    df_code: Annotated[str, "Python code that generates a DataFrame from the dataset"] = ''
    # Results / Artifacts
    df_handle: Annotated[List[str], "List of registered DataFrame names"] = []
    df_meta: Annotated[List[Dict], "Metadata for each DataFrame (schema/shape/columns, etc.)", operator.add] = []
    df_info: Annotated[Tuple[str, str], "(df_name, df_desc)"] = ('', '')
    csv_path: Annotated[List[str], "List of saved CSV file paths", operator.add] = []
    # Execution logs / Errors
    stdout: Annotated[str, "Standard output from the last DataFrame execution"] = ''
    stderr: Annotated[str, "Standard error output from the last DataFrame execution"] = ''
    attempts: Annotated[int, "Number of attempts to execute the DataFrame code"] = 0
    error_log: Annotated[str, "Error message from the last DataFrame execution"] = ''
    errors: Annotated[List[str], "List of all error messages encountered during the process"] = []


class ChartState(TypedDict, total=False):
    # Code / Input
    user_query: Annotated[str, "Original user query or question"] = ''
    dataset: Annotated[str, "Input dataset (as a dictionary or serialized string)"] = ''
    df_info: Annotated[Tuple[str, str], "(df_name, df_desc)"]
    csv_path: Annotated[str, "Path to the saved CSV file"] = ''
    df_meta: Annotated[List[Dict], "Metadata for each DataFrame (schema/shape/columns, etc.)", operator.add] = []
    chart_code: Annotated[str, "Python code that visualizes the DataFrame"] = ''
    chart_intent: Annotated[Dict, "Visualization intent/options (line, bar, axes, labels, etc.)"] = {}

    # Results / Artifacts
    image_paths: Annotated[List[str], "List of generated chart image file paths", operator.add] = []
    chart_info: Annotated[Tuple[str, str], "(chart_name, chart_desc)"] = ('', '')

    # Execution logs / Errors
    stdout: Annotated[str, "Standard output from the last chart execution"] = ''
    stderr: Annotated[str, "Standard error output from the last chart execution"] = ''
    error_logs: Annotated[str, "Error message from the last chart execution"] = ''
    errors: Annotated[List[str], "List of all error messages encountered during the process"] = []
    attempts: Annotated[int, "Number of attempts to execute the chart code"] = 0
    debug_font: Annotated[Dict, "Debug font information"] = {}


class AgentContextState(TypedDict, total=False):
    user_query: Annotated[str, "Original user query or question"] = ''
    dataset: Annotated[str, "Input dataset (as a dictionary or serialized string)"] = ''
    run_id: Annotated[str, "Unique run identifier"] = ''
    artifact_dir: Annotated[str, "Directory path for storing generated artifacts (CSV, images, etc.)"] = ''
    work_dir: Annotated[str, "Working directory path for temporary or intermediate files (./{run_id})"] = ''
    allow_scan_df: Annotated[bool, "Whether scanning/previewing the entire DataFrame is allowed"] = False

    # Progress Tracking
    attempts: Annotated[Dict, "Number of attempts per task type, e.g., {'df': int, 'chart': int}"] = {}
    generated_codes: Annotated[List[str], "generated Python code that builds DataFrame from dataset", operator.add] = []
    errors: Annotated[List[str], "List of all error messages encountered during the process"] = []

    current_chart: Annotated[Dict[str,str], "key: chart_name, value: chart_desc(refer to this chart, router decide to generate chart)"] = {}
    current_dataframe: Annotated[Dict[str,str], "key: df_name, value: df_desc(refer to this df, router decide to generate df)"] = {}
    previous_node: Annotated[str, "Previous node (e.g., 'df_exec'|'chart_exec'|...)"] = ''
    next_action: Annotated[str, "Routing key (e.g., 'to_df_gen'|'to_chart_gen'|'finish')"] = ''