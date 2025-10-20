import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import List, Dict, Any

from app.base_node.env_model import Env
from app.base_node.logger import RunLogger
from app.analyst_agent.react_code_agent.code_executor_node import (
    DataFrameCodeExecutorNode,
    ChartCodeExecutorNode,
)


def _abs(*paths: str) -> str:
    return os.path.abspath(os.path.join(*paths))


def run_one_metric(env: Env, metric_id: str) -> Dict[str, Any]:
    """Run DF executor then Chart executor for a synthetic metric in isolation.

    Returns a dict with csv_path, img_path, and any error string.
    """
    df_node = DataFrameCodeExecutorNode(verbose=True, env=env)
    chart_node = ChartCodeExecutorNode(verbose=True, env=env)

    # Simple dataset and df code that writes a CSV using save_df
    dataset = json.dumps([
        {"label": "A", "value": 1},
        {"label": "B", "value": 3},
        {"label": "C", "value": 2},
    ], ensure_ascii=False)

    df_code = (
        "df_name = \"smoke_df\"\n"
        "import json\n"
        "import pandas as pd\n"
        "data = json.loads(INPUT_DATA)\n"
        "df = pd.DataFrame(data)\n"
        "RESULT_DF = df\n"
        "save_df(RESULT_DF, df_name)\n"
    )

    df_state = {
        "user_query": "smoke test df",
        "run_id": metric_id,  # per-metric isolation
        "dataset": dataset,
        "df_code": df_code,
        "df_name": "smoke_df",
        "df_desc": "Synthetic DF for concurrency test",
        "allow_scan_df": False,
    }

    try:
        df_result = df_node(df_state)
        if hasattr(df_result, "update"):
            df_state_out = getattr(df_result, "update", {}) or {}
        else:
            df_state_out = df_result or {}
        csv_path = df_state_out.get("csv_path", "")
    except Exception as e:
        return {"metric_id": metric_id, "error": f"DF exec error: {e}", "csv_path": "", "img_path": ""}

    # Minimal chart code that reads the CSV and saves a PNG
    chart_code = (
        "import pandas as pd\n"
        "import matplotlib.pyplot as plt\n"
        f"df = pd.read_csv(r\"{csv_path}\")\n"
        "fig, ax = plt.subplots(figsize=(4, 3))\n"
        "ax.bar(df['label'], df['value'])\n"
        "ax.set_title('smoke')\n"
        "save_chart(filename='smoke.png', dpi=100)\n"
    )

    chart_state = {
        "user_query": "smoke test chart",
        "run_id": metric_id,
        "chart_code": chart_code,
    }

    try:
        chart_result = chart_node(chart_state)
        if hasattr(chart_result, "update"):
            chart_state_out = getattr(chart_result, "update", {}) or {}
        else:
            chart_state_out = chart_result or {}
        img_path = chart_state_out.get("img_path", "")
        return {"metric_id": metric_id, "error": "", "csv_path": csv_path, "img_path": img_path}
    except Exception as e:
        return {"metric_id": metric_id, "error": f"Chart exec error: {e}", "csv_path": csv_path, "img_path": ""}


def main():
    # Place artifacts under test_data/users/<user>/<metric_id>
    work_dir = _abs("test_data")
    user_id = f"SMOKE_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    logger = RunLogger(base_name="concurrency_smoke")
    env = Env(user_id=user_id, work_dir=work_dir, run_logger=logger)

    metric_ids = [f"metric_{i}" for i in range(4)]

    results: List[Dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=len(metric_ids)) as ex:
        futs = [ex.submit(run_one_metric, env, mid) for mid in metric_ids]
        for f in as_completed(futs):
            results.append(f.result())

    ok, errs = 0, []
    for r in results:
        metric_id = r["metric_id"]
        csv_path, img_path, err = r.get("csv_path"), r.get("img_path"), r.get("error")
        csv_ok = bool(csv_path and os.path.isfile(csv_path))
        img_ok = bool(img_path and os.path.isfile(img_path))
        if not err and csv_ok and img_ok:
            ok += 1
        else:
            errs.append({"metric_id": metric_id, "error": err, "csv_ok": csv_ok, "img_ok": img_ok})

    print("SMOKE SUMMARY:")
    print({"user_id": user_id, "ok": ok, "total": len(metric_ids)})
    if errs:
        print("FAILURES:")
        for e in errs:
            print(e)


if __name__ == "__main__":
    main()
