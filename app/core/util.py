import os
from pathlib import Path
from typing import Optional, Union, Iterable

import yaml
from langchain_core.prompts import ChatPromptTemplate

CORE_DIR = Path(__file__).resolve().parent
APP_DIR = CORE_DIR.parent


def _resolve_path(path_like: Union[str, Path], *, search_roots: Optional[Iterable[Path]] = None) -> Path:
    """
    Resolve a path that may be absolute or relative to one of the provided roots.
    Falls back to the first candidate if none exist to preserve historical behaviour.
    """
    candidate = Path(path_like)
    if candidate.is_absolute():
        return candidate

    roots = list(search_roots or ())
    if not roots:
        roots = [CORE_DIR, APP_DIR]

    for root in roots:
        resolved = root / candidate
        if resolved.exists():
            return resolved

    # If nothing matched, return the first candidate (typically under CORE_DIR)
    return roots[0] / candidate


def get_chat_prompt_yaml(file_path: Union[str, Path]) -> list[tuple[str, str]]:
    resolved = _resolve_path(file_path)
    with resolved.open("r", encoding="utf8") as f:
        yaml_content = yaml.safe_load(f)
        return [(message["role"], message["content"]) for message in yaml_content["messages"]]


def load_prompt_template(prompt_path: Union[str, Path]) -> ChatPromptTemplate:
    prompt_yaml = get_chat_prompt_yaml(prompt_path)
    return ChatPromptTemplate.from_messages(prompt_yaml)


def to_relative_path(abs_path: str, base_dir: Optional[str] = None, prefix: Optional[str] = None) -> str:
    """
    절대경로를 base_dir 기준 상대경로로 변환하고,
    원하는 prefix 디렉토리를 상대 경로 앞에 붙인다.

    - base_dir이 None이면 현재 작업 디렉토리(Path.cwd())를 기준으로 한다.
    - prefix가 주어지면 결과 앞에 prefix를 붙인다.
    """
    abs_path = Path(abs_path).resolve()
    base_dir = Path(base_dir).resolve() if base_dir else Path.cwd()

    try:
        rel_path = abs_path.relative_to(base_dir)
    except ValueError:
        rel_path = Path(abs_path.name)

    if prefix:
        return str(Path(prefix) / rel_path)
    return str(rel_path)


def is_alert(status) -> bool:
    """
    Utility used by react_code_agent nodes to check for alert conditions on status payloads.
    Accepts either dicts or objects with a status attribute.
    """
    try:
        if status is None:
            return False
        if isinstance(status, dict):
            return str(status.get("status", "")).lower() == "alert"
        return str(getattr(status, "status", "")).lower() == "alert"
    except Exception:
        return False
