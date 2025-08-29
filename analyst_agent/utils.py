import yaml
from langchain_core.prompts import ChatPromptTemplate
import os
from pathlib import Path
from typing import Optional

base_dir = os.path.dirname(__file__)

def get_chat_prompt_yaml(file_path):
    with open(file_path, "r", encoding='utf8') as f:
        yaml_content = yaml.safe_load(f)
        return [(message['role'], message['content']) for message in yaml_content['messages']]


def load_prompt_template(prompt_filename: str) -> ChatPromptTemplate:
    prompt_path = os.path.join(base_dir, prompt_filename)
    prompt_yaml = get_chat_prompt_yaml(prompt_path)
    return ChatPromptTemplate.from_messages(prompt_yaml)




def to_relative_path(abs_path: str, base_dir: Optional[str] = None) -> str:
    """
    절대경로를 base_dir 기준 상대경로로 변환한다.
    
    base_dir이 None이면 현재 작업 디렉토리(Path.cwd())를 기준으로 한다.
    """
    abs_path = Path(abs_path).resolve()
    base_dir = Path(base_dir).resolve() if base_dir else Path.cwd()

    try:
        return str(abs_path.relative_to(base_dir))
    except ValueError:
        return abs_path.name