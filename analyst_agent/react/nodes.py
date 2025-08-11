import io, re, logging, time, warnings, traceback
from typing import Dict, Any, Optional
from contextlib import redirect_stdout
import os
import pandas as pd
import matplotlib.pyplot as plt
from .state import AgentContextState
from ..base import BaseNode
from ..react.state import ReactReportState

class CodeExecutorNode(BaseNode):

    FONT_WARN_PATTERN = re.compile(r"(Glyph .* missing|findfont:.*Font family .* not found)", re.I)
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
        ts = int(time.time())
        safe_name = self._safe_name(name)
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

    def _create_exec_env(self, registry: Dict[str, Any], state: ReactReportState) -> Dict[str, Any]:
        def register_df(df: pd.DataFrame, name: str, metadata: Optional[Dict[str, Any]] = None):
            assert isinstance(df, pd.DataFrame), "register_df expects a DataFrame"
            info = self._write_csv(df, name, state["artifact_dir"])
            registry["dataframes"][info["name"]] = {**info, "metadata": metadata or {}}
            if "primary_df" not in registry:
                registry["primary_df"] = {"name": info["name"], "df_ref": df, "metadata": metadata or {}}

        def publish_df(df: pd.DataFrame, name: str):
            register_df(df, name)

        env = {
            "__builtins__": __builtins__,
            "pd": pd,
            "plt": plt,
            "register_df": register_df,
            "publish_df": publish_df,
        }
        return env

    def run(self, state: AgentContextState) -> AgentContextState:
        gcodes = state['generated_codes']

        if not isinstance(gcodes, list) or not gcodes:
            return{
                "phase": state["phase"] or "executing",
                "attempts": state["attempts"] or {},
                "last_error": "No code provided (generated_codes is empty)",
                "errors": ["No code provided (generated_codes is empty)"],
            }

        code = gcodes[-1]

        if not isinstance(code, str) or not code.strip():
            return{
                "phase": state["phase"] or "executing",
                "attempts": state["attempts"] or {},
                "last_error": "No code provided (generated_codes is empty)",
                "errors": ["No code provided (generated_codes is empty)"],
            }

        stdout_stream = io.StringIO()
        stderr_stream = io.StringIO()
        log_stream = io.StringIO()

        logger = logging.getLogger("matplotlib.font_manager")
        handler = logging.StreamHandler(log_stream)
        logger.addHandler(handler)

        try:
            plt.clf()
            plt.close("all")
        except Exception as e:
            pass
        
        registry: Dict[str, Any] = {"dataframes": {}, "images": []}
        error_list: List[str] = []

        try:
            with redirect_stdout(stdout_stream), redirect_stderr(stderr_stream):
                with warnings.catch (record=True) as warning_list:
                    warnings.simplefilter("always")
                    g_env = self._create_exec_env(registry, state)
                    l_env: Dict[str, Any] = {}
                    try:
                        exec(code, g_env, l_env)
                    except Exception as e:
                        error_trace = traceback.format_exc()
                        error = f"{str(e)}\n{error_trace}"
                        error_list.append(error)
                    
                    warn_hit = any(
                        self.FONT_WARN_PATTERN.search(str(warn.message)) for warn in warning_list
                    )
                    log_hit = self.FONT_WARN_PATTERN.search(log_stream.getvalue())
                    if warn_hit or log_hit:
                        # 원형은 경고도 재시도 루프를 위해 "에러"로 간주
                        error_msg = (log_stream.getvalue() or "") + (("\n" + warnings_text) if warnings_text else "")
                        last_error_msg = (error_msg.strip() or "Warnings detected")
                        error_list.append(f"matplotlib_font_issue: warn_hit={warn_hit}, log_hit={log_hit}")

        finally:
            logger.removeHandler(handler)
            try:
                plt.close("all")
            except Exception:
                pass
        
        # check local_env for RESULT_DF and register it as the primary result DataFrame.
        if "primary_df" not in registry and 'l_env' in locals() and isinstance(l_env, dict):
            if "RESULT_DF" in l_env:
                try:
                    df = l_env["RESULT_DF"]
                    self._create_exec_env(registry, state)["register_df"](df, "result")
                except Exception as e:
                    error_list.append(f"Failed to register RESULT_DF: {e}")

        # scanning is allowed, search l_env for the first pandas DataFrame (optional)
        if state["allow_scan_df"] and not registry["dataframes"] and 'l_env' in locals() and isinstance(l_env, dict):
            for k, v in l_env.items():
                try:
                    if isinstance(v, pd.DataFrame):
                        self._create_exec_env(registry, state)["register_df"](v, f"auto_{k}")
                        break
                except Exception:
                    continue
        # DF 집계
        df_handles: List[str] = []
        df_metas: List[Dict[str, Any]] = []
        csv_paths: List[str] = []
        for name, info in registry["dataframes"].items():
            df_handles.append(name)
            meta = {
                "name": name,
                "path": info.get("path"),
                "rows": info.get("rows"),
                "schema": info.get("schema"),
                "columns": info.get("columns"),
                "shape": info.get("shape"),
                "format": info.get("format", "csv"),
                "extra": (info.get("meta") or {}),
            }
            df_metas.append(meta)
            if info.get("path"):
                csv_paths.append(info["path"])

        image_paths: List[str] = list(registry["images"])

        attempts: Dict[str, int] = dict(state.get("attempts") or {})
        if df_handles:
            attempts["df"] = int(attempts.get("df", 0)) + 1
        if image_paths:
            attempts["chart"] = int(attempts.get("chart", 0)) + 1

        combined_stderr = "\n".join(
            s for s in [stderr_stream.getvalue(), log_stream.getvalue()] if s
        ).strip()

        return {
            "phase": "executing",
            "attempts": attempts,
            "generated_codes": gcodes,
            "df_handle": df_handles,
            "df_meta": df_metas,
            "csv_path": csv_paths,
            "image_paths": image_paths,
            "last_stdout": stdout_stream.getvalue(),
            "last_stderr": combined_stderr,
            "last_error": last_error_msg,
            "errors": error_list,
        }


