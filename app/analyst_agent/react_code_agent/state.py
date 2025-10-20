from typing import TypedDict, Annotated, List, Dict, Tuple, Literal
import operator
from pydantic import BaseModel, Field

'''
workdir structure: 
/root/
└── users/
    └── {user_id}/
        └── {run_id}/
            ├── artifacts/      # 실행 결과물 (CSV, 이미지, 리포트 등)
            └── logs/


example
/root/users/{user_id}/2025-08-03_160530/
  ├─ artifacts/
  │   ├─ 1723871120_df.csv
  │   └─ 1723871121_chart.png
  └─ logs/
      └─ 2025-08-03_160530.log
'''

class Status(BaseModel):
    status: Literal["normal", "alert"] = "normal"
    message: str = "Everything is running smoothly."


class DataFrameState(TypedDict, total=False):
    # Code / Input
    user_query: Annotated[str, "Original user query or question"] = ''
    run_id: Annotated[str, "Unique run identifier"] = ''
    dataset: Annotated[str, "Input dataset (as a dictionary or serialized string)"] = ''
    df_code: Annotated[str, "Python code that generates a DataFrame from the dataset"] = ''
    df_name: Annotated[str, "DataFrame name"] = ''
    df_desc: Annotated[str, "DataFrame description"] = ''
    status: Annotated[Status, "Status of the DataFrame execution"] = Status(status="normal", message="Everything is running smoothly.")
    # Results / Artifacts
    df_handle: Annotated[List[str], "List of registered DataFrame names"] = []
    df_meta: Annotated[Dict, "Metadata for each DataFrame (schema/shape/columns, etc.)"] = {}
    csv_path: Annotated[str, "List of saved CSV file paths", operator.add] = ''
    # Execution logs / Errors
    stdout: Annotated[str, "Standard output from the last DataFrame execution"] = ''
    stderr: Annotated[str, "Standard error output from the last DataFrame execution"] = ''
    attempts: Annotated[int, "Number of attempts to execute the DataFrame code"] = 0
    error_log: Annotated[str, "Error message from the last DataFrame execution"] = ''
    errors: Annotated[List[str], "List of all error messages encountered during the process"] = []
    cost: Annotated[float, "Total cost of the DataFrame execution"] = 0.0


class ChartState(TypedDict, total=False):
    # Code / Input
    user_query: Annotated[str, "Original user query or question"] = ''
    run_id: Annotated[str, "Unique run identifier"] = ''
    dataset: Annotated[str, "Input dataset (as a dictionary or serialized string)"] = ''
    df_name : Annotated[str, "DataFrame name"] = ''
    df_desc: Annotated[str, "DataFrame description"] = ''
    df_meta: Annotated[Dict, "Metadata for each DataFrame (schema/shape/columns, etc.)"] = {}
    df_code: Annotated[str, "Python code to generate the DataFrame"] = ''
    csv_path: Annotated[str, "Path to the saved CSV file"] = ''
    chart_code: Annotated[str, "Python code that visualizes the DataFrame"] = ''
    chart_intent: Annotated[Dict, "Visualization intent/options (line, bar, axes, labels, etc.)"] = {}
    status: Annotated[Status, "Status of the Chart execution"] = Status(status="normal", message="Everything is running smoothly.")

    # Results / Artifacts
    img_path: Annotated[str, "Path to the saved image file"] = ''
    chart_name: Annotated[str, "Chart name"] = ''
    chart_desc: Annotated[str, "Chart description"] = ''
    cost: Annotated[float, "Total cost of the Chart execution"] = 0.0

    # Execution logs / Errors
    stdout: Annotated[str, "Standard output from the last chart execution"] = ''
    stderr: Annotated[str, "Standard error output from the last chart execution"] = ''
    error_log: Annotated[str, "Error message from the last chart execution"] = ''
    errors: Annotated[List[str], "List of all error messages encountered during the process"] = []
    attempts: Annotated[int, "Number of attempts to execute the chart code"] = 0
    debug_font: Annotated[Dict, "Debug font information"] = {}
    


class AgentContextState(TypedDict, total=False):
    user_query: Annotated[str, "Original user query or question"] = ''
    dataset: Annotated[str, "Input dataset (as a dictionary or serialized string)"] = ''
    run_id: Annotated[str, "Unique run identifier"] = ''
    allow_scan_df: Annotated[bool, "Whether scanning/previewing the entire DataFrame is allowed"] = False
    status: Annotated[Status, "Status of the agent"] = Status(status="normal", message="Everything is running smoothly.")
    cost: Annotated[float, "Total cost of the agent"] = 0.0

    # Progress Tracking
    attempts: Annotated[Dict, "Number of attempts per task type, e.g., {'df': int, 'chart': int}"] = {}
    errors: Annotated[List[str], "List of all error messages encountered during the process"] = []

    chart_name: Annotated[str, "chart name"] = ''
    chart_desc: Annotated[str, "chart description"] = ''
    chart_code: Annotated[str, "Python code that visualizes the DataFrame"] = ''
    img_path: Annotated[str, "Path to the saved image file"] = ''
    csv_path: Annotated[str, "Path to the saved CSV file"] = ''
    df_name: Annotated[str, "DataFrame name"] = ''
    df_desc: Annotated[str, "DataFrame description"] = ''
    df_code: Annotated[str, "Python code that generates a DataFrame from the dataset"] = ''
    df_meta: Annotated[Dict, "Metadata for each DataFrame (schema/shape/columns, etc.)"] = {}
    previous_node: Annotated[str, "Previous node (e.g., 'df_exec'|'chart_exec'|'router'|...)"] = ''
    next_action: Annotated[str, "Routing key (e.g., 'to_df_gen'|'to_chart_gen'|'finish')"] = ''