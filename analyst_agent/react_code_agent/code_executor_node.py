import io, re, logging, time, warnings, traceback
from typing import Dict, Any
from contextlib import redirect_stdout, redirect_stderr
import os, json
import pandas as pd
import matplotlib.font_manager as fm
import matplotlib as mpl
import matplotlib.pyplot as plt
from analyst_agent.react_code_agent.state import DataFrameState, ChartState
from base_node.base import BaseNode

class DataFrameCodeExecutorNode(BaseNode):
    def __init__(self, verbose: bool = False, **kwargs):
        super().__init__(verbose=verbose, **kwargs)

    @staticmethod
    def _safe_name(name: str) -> str:
        safe = re.sub(r'[^a-zA-Z0-9_]', "_", name or "").strip("_") or "df"
        return safe[:50]

    @staticmethod
    def _abs(*paths: str) -> str:
        return os.path.abspath(os.path.join(*paths))

    def _write_csv(self, df: pd.DataFrame, name: str, artifact_dir: str) -> Dict[str, Any]:
        '''
        DataFrame을 CSV 파일로 저장하고, 저장된 파일의 메타데이터를 반환합니다.
        '''
        ts = int(time.time())
        safe_name = self._safe_name(name)
        os.makedirs(self._abs(artifact_dir), exist_ok=True)
        path = self._abs(artifact_dir, f"{ts}_{safe_name}.csv")
        df.to_csv(path, index=True, encoding="utf-8-sig")
        try:
            schema = {k: str(v) for k, v in df.dtypes.to_dict().items()}
            #self.log(f"Wrote CSV to {self._abs(artifact_dir, f"{ts}_{safe_name}.csv")}")
        except Exception as e:
            schema = None
        return {
            "name": safe_name,
            "path": path,
            "format": "csv",
            "rows": int(len(df)),
            "schema": schema,
        }

    def _collect_df_meta(self, df: pd.DataFrame, name: str, max_cols: int = 30, sample_rows: int = 5) -> dict:
        '''
        output format:
        {
            "name": name,
            "rows": rows,
            "cols": cols,
            "columns": columns,
            "schema": schema,
            "memory": int(df.memory_usage(deep=True).sum()),
            ----------- optional -----------
            "nulls": nulls,
            "sample": sample,
        }
        '''
        cols = int(df.shape[1])
        rows = int(len(df))
        schema = [{"name": c, "dtype": str(df[c].dtype)} for c in list(df.columns)[:max_cols]]
        columns = df.columns.tolist()
        out = {
            "name": name,
            "rows": rows,
            "cols": cols,
            "columns": columns,
            "schema": schema,
            "memory": int(df.memory_usage(deep=True).sum()),
        }
        try:
            nulls = df.isna().sum()
            out["nulls"] = {k: int(nulls[k]) for k in list(df.columns)[:max_cols]}
        except Exception:
            pass
        if sample_rows > 0:
            try:
                out["sample"] = df.head(sample_rows).to_dict(orient="records")
            except Exception:
                pass
        return out



    def _create_exec_env_for_df(self, registry, artifact_dir, dataset, debug_on: bool=False):

        def save_df(df: pd.DataFrame, name: str):

            info = self._write_csv(df, name, artifact_dir)
            if debug_on:
                meta = self._collect_df_meta(df, name, max_cols=30, sample_rows=5)
                entry = {**info, **meta}
            else:
                entry = info
            registry["dataframes"][entry["name"]] = entry
            # initialize primary_df for monitoring 
            if "primary_df" not in registry:
                registry["primary_df"] = {"name": entry["name"], "df_ref": df}

        return {
            "__builtins__": __builtins__,
            "pd": pd,
            "json": json, 
            "save_df": save_df,
            "INPUT_DATA": dataset,
            }


    def run(self, state: DataFrameState) -> DataFrameState:
        code = state.get("df_code")
        if not code or not code.strip():
            self.logger.warning("No df_code provided")
            return {"error_logs": "No df_code provided"}

        stdout_stream, stderr_stream = io.StringIO(), io.StringIO()
        registry: Dict[str, Any] = {"dataframes": {}}
        errors: list[str] = []
        error_log = ""

        try:
            work_dir = self.env.work_dir
            user_id = self.env.user_id
            run_id = state.get("run_id")
            dataset = state.get("dataset")
            artifact_dir = self._abs(work_dir, "users", user_id, run_id, "artifacts")
            g_env = self._create_exec_env_for_df(registry, artifact_dir, dataset)  # offer save_df
            l_env: Dict[str, Any] = {}

            self.logger.info("Executing df_code …")
            with redirect_stdout(stdout_stream), redirect_stderr(stderr_stream):
                try:
                    exec(code, g_env, l_env)
                except Exception:
                    err = traceback.format_exc()
                    errors.append(err)
                    error_log = "DF exec failed"
                    self.logger.exception("DataFrame execution failed")

            # check local_env for RESULT_DF and save it as the primary result DataFrame.
            if "primary_df" not in registry and isinstance(l_env, dict) and "RESULT_DF" in l_env:
                try:
                    df = l_env["RESULT_DF"]
                    g_env["save_df"](df, "result")
                    self.logger.info("RESULT_DF saved as primary result")
                except Exception as e:
                    errors.append(f"Failed to save RESULT_DF: {e}")
                    self.logger.exception("Failed to save RESULT_DF")

            # scanning is allowed, search l_env for the first pandas DataFrame (optional)
            if state.get("allow_scan_df", True) and not registry["dataframes"]:
                for k, v in (l_env or {}).items():
                    if isinstance(v, pd.DataFrame):
                        g_env["save_df"](v, f"auto_{k}")
                        self.logger.info(f"Auto-detected DataFrame saved as auto_{k}")
                        break

            # collect metas
            df_handles, df_meta, csv_path = [], {}, ''
            for name, info in registry["dataframes"].items():
                df_handles.append(name)
                df_meta = {
                    "name": name, 
                    "path": info.get("path"),
                    "rows": info.get("rows"), 
                    "schema": info.get("schema"),
                    "format": info.get("format", "csv")
                }
                if info.get("path"):
                    csv_path = info.get("path") 
            self.logger.debug(f"Collected DF meta: {df_meta}")


            attempts = (state.get("attempts", 0)) + 1
            self.log(message=stdout_stream.getvalue())
            self.logger.info("DataFrame execution node completed")
            self.logger.debug(f"DF handles: {df_handles}")
            self.logger.debug(f"DF meta: {df_meta}")

            state['df_handle'] = df_handles
            state['df_meta'] = df_meta
            state['csv_path'] = csv_path
            state['stdout'] = stdout_stream.getvalue()
            state['stderr'] = stderr_stream.getvalue().strip()
            state['error_log'] = error_log if errors else ""
            state['errors'] = (state.get("errors") or []) + errors
            state['attempts'] = attempts

            return state
        finally:
            try:
                plt.close("all")
            except: 
                pass


class ChartCodeExecutorNode(BaseNode):
    FONT_WARN_PATTERN = re.compile(r"(Glyph .* missing|findfont:.*Font family .* not found)", re.I)

    FONT_CANDIDATES: Dict[str, list[str]] = {
        "NanumGothic": [
            "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
            "/usr/local/share/fonts/NanumGothic.ttf",
            "/System/Library/Fonts/Supplemental/NanumGothic.ttf",
        ],
        "Noto Sans CJK KR": [
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
        ],
        # cannot find font (basic font)
        "DejaVu Sans": []
    }
    def __init__(self, verbose: bool = False, **kwargs):
        super().__init__(verbose=verbose, **kwargs)

    @staticmethod
    def _safe_name(name: str) -> str:
        safe = re.sub(r'[^a-zA-Z0-9_]', "_", name or "").strip("_") or "df"
        return safe[:50]

    @staticmethod
    def _abs(*paths: str) -> str:
        return os.path.abspath(os.path.join(*paths))

    def _auto_apply_korean_font(self) -> dict[str, str]:
        chosen = {"family": "NanumGothic", "path": ""}

        def _apply_by_path(path: str) -> bool:
            if os.path.exists(path):
                try:
                    # ttf register
                    fm.fontManager.addfont(path)
                    fam = fm.FontProperties(fname=path).get_name()
                    fm._rebuild()
                    # rcParams update
                    mpl.rcParams["font.family"] = fam
                    mpl.rcParams["font.sans-serif"] = [fam]
                    mpl.rcParams["axes.unicode_minus"] = False
                    chosen["family"], chosen["path"] = fam, path
                    return True
                except Exception:
                    return False
            return False

        # 0) hard path
        if _apply_by_path("/usr/share/fonts/truetype/nanum/NanumGothic.ttf"):
            return chosen

        # 1) candidate paths
        for fam, paths in self.FONT_CANDIDATES.items():
            for p in paths:
                if _apply_by_path(p):
                    return chosen

        # 2) system registered font name (if possible)
        for fam in ("NanumGothic", "Noto Sans CJK KR", "DejaVu Sans"):
            try:
                fm.findfont(fam, fallback_to_default=(fam == "DejaVu Sans"))
                mpl.rcParams["font.family"] = fam
                mpl.rcParams["font.sans-serif"] = [fam]
                mpl.rcParams["axes.unicode_minus"] = False
                chosen["family"], chosen["path"] = fam, ""
                return chosen
            except Exception:
                continue

        # 3) final fallback
        mpl.rcParams["font.family"] = "DejaVu Sans"
        mpl.rcParams["font.sans-serif"] = ["DejaVu Sans"]
        mpl.rcParams["axes.unicode_minus"] = False
        chosen["family"] = "DejaVu Sans"
        return chosen

    def _create_exec_env_for_chart(self, registry, artifact_dir: str, applied_font: dict):
        def save_chart(fig: plt.Figure = None, filename=None, dpi=170):
            ts = int(time.time())
            name = filename or f"chart_{ts}.png"
            os.makedirs(artifact_dir, exist_ok=True)
            path = os.path.join(artifact_dir, name)
            if fig is None:
                plt.savefig(path, dpi=dpi, bbox_inches="tight")
            else:
                fig.savefig(path, dpi=dpi, bbox_inches="tight")
            registry["images"].append(path)
            return path

        return {
            "__builtins__": __builtins__,
            "pd": pd,
            "plt": plt,
            "save_chart": save_chart,
            "use_korean_font": lambda: applied_font.get("family", ""),
            "_applied_font": dict(applied_font),
        }

    def run(self, state: ChartState) -> ChartState:
        code = state["chart_code"]
        if not code or not code.strip():
            self.logger.warning("No chart_code provided")
            return {"error_log": "No chart_code provided"}

        stdout_stream, stderr_stream, log_stream = io.StringIO(), io.StringIO(), io.StringIO()
        # matplotlib.font_manager 로그 캡처(폰트 진단용)
        mpl_logger = logging.getLogger("matplotlib.font_manager")
        mpl_handler = logging.StreamHandler(log_stream)
        mpl_logger.addHandler(mpl_handler)

        registry: Dict[str, Any] = {"images": []}
        errors: list[str] = []
        error_log = ""

        try:
            plt.clf()
            plt.close("all")
            # korean font
            applied = self._auto_apply_korean_font()
            plt.rcParams["axes.unicode_minus"] = False
            work_dir = self.env.work_dir
            user_id = self.env.user_id
            run_id = state.get("run_id")
            artifact_dir = self._abs(work_dir, "users", user_id, run_id, "artifacts")
            g_env = self._create_exec_env_for_chart(registry, artifact_dir, applied)
            l_env: Dict[str, Any] = {}

            self.logger.info("Executing chart_code …")

            with redirect_stdout(stdout_stream), redirect_stderr(stderr_stream):
                with warnings.catch_warnings(record=True) as warning_list:
                    warnings.simplefilter("always")
                    try:
                        exec(code, g_env, l_env)
                    except Exception:
                        errors.append(traceback.format_exc())
                        error_log = "Chart exec failed"
                        self.logger.exception("Chart execution failed")

            # Font warnings are considered errors (retry routing)
            warn_hit = any(self.FONT_WARN_PATTERN.search(str(w.message)) for w in warning_list)
            log_hit = self.FONT_WARN_PATTERN.search(log_stream.getvalue())
            if warn_hit or log_hit:
                msg = f"matplotlib_font_issue: warn_hit={warn_hit}, log_hit={bool(log_hit)}"
                errors.append(msg)
                error_log = error_log or "Font warning detected"
                self.logger.warning(msg)

            attempts = (state.get("attempts", 0)) + 1
            
            if error_log:
                self.logger.error("Error_log: ", error_log)
            
            if errors:
                self.logger.error("Errors: ", errors)

            state['img_path'] = registry["images"]
            state['stdout'] = stdout_stream.getvalue()
            state['stderr'] = "\n".join(s for s in [stderr_stream.getvalue(), log_stream.getvalue()] if s).strip()
            state['error_log'] = error_log if errors else ""
            state['errors'] = (state.get("errors") or []) + errors
            state['attempts'] = attempts
            state['debug_font'] = applied

            return state

        finally:
            mpl_logger.removeHandler(mpl_handler)
            try: plt.close("all")
            except: pass

if __name__ == "__main__":
    import sys
    import os 
    from inspect import cleandoc
    sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "../..")))    
    chart_node = ChartCodeExecutorNode(verbose=True)
    chart_code = cleandoc("""
import pandas as pd
import matplotlib.pyplot as plt

df = pd.DataFrame({
    "과목": ["수학", "영어", "국어", "과학"],
    "점수": [88, 92, 81, 95]
})

fig, ax = plt.subplots(figsize=(6, 4))
ax.bar(df["과목"], df["점수"])
ax.set_title("과목별 점수")
ax.set_xlabel("과목")
ax.set_ylabel("점수")
fig.tight_layout()

# 실행기가 주입하는 헬퍼
save_chart(filename="bar_example.png", dpi=170)
""")
    chart_state : ChartState = {
    "chart_code": chart_code,
    "artifact_dir": "./artifacts_test",
    "chart_intent":{},
    "image_paths": [],
    "attempts": 0,
    "last_stdout": "",
    "last_stderr": "",
    "last_error": "",
    "errors": [],
}
    chart_result = chart_node.run(state=chart_state)
    print(chart_result)