import io, re, logging, time, warnings, traceback
from typing import Dict, Any, Optional
from contextlib import redirect_stdout, redirect_stderr
import os
import pandas as pd
import matplotlib.pyplot as plt
from .state import DataFrameState, ChartState
from ..base import BaseNode

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
        cols = int(df.shape[1])
        rows = int(len(df))
        schema = [{"name": c, "dtype": str(df[c].dtype)} for c in list(df.columns)[:max_cols]]
        out = {
            "name": name,
            "rows": rows,
            "cols": cols,
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



    def _create_exec_env_for_df(self, registry, state, debug_on: bool=False):

        def register_df(df: pd.DataFrame, name: str):

            info = self._write_csv(df, name, state["artifact_dir"])
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
            "register_df": register_df
            }


    def run(self, state: DataFrameState) -> DataFrameState:
        code = state.get("dataframe_code")  # 분리된 슬롯
        if not code or not code.strip():
            return {"df_last_error": "No df_code provided"}

        stdout_stream, stderr_stream = io.StringIO(), io.StringIO()
        registry: Dict[str, Any] = {"dataframes": {}}
        errors: list[str] = []
        last_err = ""

        try:
            g_env = self._create_exec_env_for_df(registry, state)  # register_df만 제공
            l_env: Dict[str, Any] = {}
            with redirect_stdout(stdout_stream), redirect_stderr(stderr_stream):
                try:
                    exec(code, g_env, l_env)
                except Exception:
                    err = traceback.format_exc()
                    errors.append(err); last_err = "DF exec failed"

            # check local_env for RESULT_DF and register it as the primary result DataFrame.
            if "primary_df" not in registry and isinstance(l_env, dict) and "RESULT_DF" in l_env:
                try:
                    df = l_env["RESULT_DF"]
                    g_env["register_df"](df, "result")
                except Exception as e:
                    errors.append(f"Failed to register RESULT_DF: {e}")

            # scanning is allowed, search l_env for the first pandas DataFrame (optional)
            if state.get("allow_scan_df", True) and not registry["dataframes"]:
                for k, v in (l_env or {}).items():
                    if isinstance(v, pd.DataFrame):
                        g_env["register_df"](v, f"auto_{k}"); break

            # collect metas
            df_handles, df_metas, csv_paths = [], [], []
            for name, info in registry["dataframes"].items():
                df_handles.append(name)
                df_metas.append({
                    "name": name, "path": info.get("path"),
                    "rows": info.get("rows"), "schema": info.get("schema"),
                    "format": info.get("format", "csv")
                })
                if info.get("path"): csv_paths.append(info["path"])


            attempts = (state['attempts'] or 0) + 1

            return {
                "df_handle": df_handles,
                "df_meta": df_metas,
                "csv_path": csv_paths,
                "stdout": stdout_stream.getvalue(),
                "stderr": stderr_stream.getvalue().strip(),
                "last_error": last_err if errors else "",
                "errors": (state.get("errors") or []) + errors,
                "attempts": attempts,
            }
        finally:
            try: plt.close("all")
            except: pass


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

    def _auto_apply_korean_font(self) -> Dict[str, str]:
        """
        우선순위:
        0) /usr/share/.../NanumGothic.ttf (하드 경로)
        1) 'NanumGothic' 패밀리명
        2) FONT_CANDIDATES (이름 → 경로 순서)
        3) 'DejaVu Sans' (fallback)
        성공 시 rcParams에 적용. 반환: {"family": <적용이름>, "path": <경로 or "">}
        """
        chosen = {"family": "NanumGothic", "path": ""}

        # 0) Hard path lookup
        hard = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
        if os.path.exists(hard):
            try:
                fam = fm.FontProperties(fname=hard).get_name()
                plt.rcParams["font.family"] = fam
                plt.rcParams["axes.unicode_minus"] = False
                chosen["family"], chosen["path"] = fam, hard
                return chosen
            except Exception:
                pass

        # 1) Family name lookup
        try:
            fm.findfont("NanumGothic", fallback_to_default=False)
            plt.rcParams["font.family"] = "NanumGothic"
            plt.rcParams["axes.unicode_minus"] = False
            chosen["family"] = "NanumGothic"
            return chosen
        except Exception:
            pass

        # 2) Candidate rotation
        for fam, paths in self.FONT_CANDIDATES.items():
            try:
                fm.findfont(fam, fallback_to_default=False)
                plt.rcParams["font.family"] = fam
                plt.rcParams["axes.unicode_minus"] = False
                chosen["family"] = fam
                return chosen
            except Exception:
                pass

            # Path rotation
            for p in paths:
                if os.path.exists(p):
                    try:
                        fam_name = fm.FontProperties(fname=p).get_name()
                        plt.rcParams["font.family"] = fam_name
                        plt.rcParams["axes.unicode_minus"] = False
                        chosen["family"], chosen["path"] = fam_name, p
                        return chosen
                    except Exception:
                        continue

        # 3) Fallback
        try:
            fm.findfont("DejaVu Sans", fallback_to_default=True)
            plt.rcParams["font.family"] = "DejaVu Sans"
            plt.rcParams["axes.unicode_minus"] = False
            chosen["family"] = "DejaVu Sans"
        except Exception:
            plt.rcParams["axes.unicode_minus"] = False

        return chosen

    def _create_exec_env_for_chart(self, registry, artifact_dir: str, applied_font: Dict[str, str], enforce: bool):
        def _reapply_font():
            if enforce:
                self._auto_apply_korean_font()
                plt.rcParams["axes.unicode_minus"] = False

        def save_chart(fig: plt.Figure = None, filename=None, dpi=170):
            # 저장 직전에 한 번 더 강제 적용(중간에 코드가 폰트를 바꿨더라도 덮어씀)
            _reapply_font()

            ts = int(time.time())
            name = filename or f"chart_{ts}.png"
            out_dir = artifact_dir
            os.makedirs(out_dir, exist_ok=True)
            path = os.path.join(out_dir, name)
            if fig is None:
                plt.savefig(path, dpi=dpi, bbox_inches="tight")
            else:
                fig.savefig(path, dpi=dpi, bbox_inches="tight")
            registry["images"].append(path)
            return path

        def use_korean_font(name_or_force: bool | str | None = None, *, path: str | None = None) -> str:
            """
            사용법:
            use_korean_font(True)                      # NanumGothic 우선 강제(실패 시 자동 폴백)
            use_korean_font("NanumGothic")             # 특정 패밀리명 적용
            use_korean_font(path="/.../NanumGothic.ttf")  # 특정 파일 경로 적용
            use_korean_font()                          # 자동 후보 탐색
            반환: 적용된 폰트 패밀리명(없으면 "")
            """
            # True인 경우: NanumGothic 우선 강제 시도 → 실패 시 자동 폴백
            if name_or_force is True:
                hard = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
                if os.path.exists(hard):
                    try:
                        fam = fm.FontProperties(fname=hard).get_name()
                        plt.rcParams["font.family"] = fam
                        plt.rcParams["axes.unicode_minus"] = False
                        return fam
                    except Exception:
                        pass
                return self._auto_apply_korean_font().get("family", "")

            # Family name
            if isinstance(name_or_force, str):
                try:
                    fm.findfont(name_or_force, fallback_to_default=False)
                    plt.rcParams["font.family"] = name_or_force
                    plt.rcParams["axes.unicode_minus"] = False
                    return name_or_force
                except Exception:
                    return self._auto_apply_korean_font().get("family", "")
            # path
            if path:
                try:
                    fam = fm.FontProperties(fname=path).get_name()
                    plt.rcParams["font.family"] = fam
                    plt.rcParams["axes.unicode_minus"] = False
                    return fam
                except Exception:
                    return self._auto_apply_korean_font().get("family", "")

            # No arguments: Auto search
            return self._auto_apply_korean_font().get("family", "")

        return {
            "__builtins__": __builtins__,
            "pd": pd,
            "plt": plt,
            "save_chart": save_chart,
            "use_korean_font": use_korean_font,
            "_applied_font": dict(applied_font),
        }

    def run(self, state: ChartState) -> ChartState:
        code = state["chart_code"]
        if not code or not code.strip():
            return {"last_error": "No chart_code provided"}

        stdout_stream, stderr_stream, log_stream = io.StringIO(), io.StringIO(), io.StringIO()
        logger = logging.getLogger("matplotlib.font_manager")
        handler = logging.StreamHandler(log_stream); logger.addHandler(handler)

        registry: Dict[str, Any] = {"images": []}
        errors: list[str] = []; last_err = ""

        try:
            plt.clf()
            plt.close("all")
            enforce = bool(state.get("enforce_korean_font", True))
            applied = {}
            if enforce:
                applied = self._auto_apply_korean_font(state)
                plt.rcParams["axes.unicode_minus"] = False
            g_env = self._create_exec_env_for_chart(registry, state, applied, enforce=True)
            l_env: Dict[str, Any] = {}

            with redirect_stdout(stdout_stream), redirect_stderr(stderr_stream):
                with warnings.catch_warnings(record=True) as warning_list:
                    warnings.simplefilter("always")
                    try:
                        exec(code, g_env, l_env)
                    except Exception:
                        errors.append(traceback.format_exc()); last_err = "Chart exec failed"

            # Font warnings are considered errors (retry routing)
            warn_hit = any(self.FONT_WARN_PATTERN.search(str(w.message)) for w in warning_list)
            log_hit = self.FONT_WARN_PATTERN.search(log_stream.getvalue())
            if warn_hit or log_hit:
                errors.append(f"matplotlib_font_issue: warn_hit={warn_hit}, log_hit={bool(log_hit)}")
                last_err = last_err or "Font warning detected"

            attempts = (state['attempts'] or 0) + 1

            return {
                "image_paths": registry["images"],
                "stdout": stdout_stream.getvalue(),
                "stderr": "\n".join(s for s in [stderr_stream.getvalue(), log_stream.getvalue()] if s).strip(),
                "last_error": last_err if errors else "",
                "errors": (state.get("errors") or []) + errors,
                "attempts": attempts,
            }
        finally:
            logger.removeHandler(handler)
            try: plt.close("all")
            except: pass