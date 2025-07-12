import yaml
from langchain_core.prompts import ChatPromptTemplate
import os

base_dir = os.path.dirname(__file__)

def get_chat_prompt_yaml(file_path):
    with open(file_path, "r", encoding='utf8') as f:
        yaml_content = yaml.safe_load(f)
        return [(message['role'], message['content']) for message in yaml_content['messages']]


def load_prompt_template(prompt_filename: str) -> ChatPromptTemplate:
    prompt_path = os.path.join(base_dir, prompt_filename)
    prompt_yaml = get_chat_prompt_yaml(prompt_path)
    return ChatPromptTemplate.from_messages(prompt_yaml)