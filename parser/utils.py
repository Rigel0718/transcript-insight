import yaml
from langchain_core.prompts import ChatPromptTemplate

import time
from functools import wraps

# base_dir = os.path.dirname(__file__)  # 이 파일 기준

def get_chat_prompt_yaml(file_path):
    with open(file_path, "r", encoding='utf8') as f:
        yaml_content = yaml.safe_load(f)
        return [(message['role'], message['content']) for message in yaml_content['messages']]


def load_prompt_template(prompt_filename: str) -> ChatPromptTemplate:
    # prompt_path = os.path.join(base_dir, "prompts", prompt_filename)
    prompt_yaml = get_chat_prompt_yaml(prompt_filename)
    return ChatPromptTemplate.from_messages(prompt_yaml)

def track_time(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"[{func.__name__}] 실행 시간: {end - start:.2f}초")
        return result
    return wrapper
