from langchain.tools import tool
from typing import Annotated
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_openai import ChatOpenAI
from analyst_agent.utils import load_prompt_template
import io
import sys
from contextlib import redirect_stdout
import matplotlib.pyplot as plt
import base64

@tool
def python_repl_tool(
    code: Annotated[str, "The python code to execute to generate your chart."],
):
    """
    Use this tool to execute Python code. It will execute the code and return the chart as a base64 encoded string.
    """
    plt.clf()
    
    f = io.StringIO()
    with redirect_stdout(f):
        try:
            exec(code, globals())
        except Exception as e:
            return f"Failed to execute. Error: {repr(e)}\n{f.getvalue()}"
    
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png')
    img_buffer.seek(0)
    img_base64 = base64.b64encode(img_buffer.read()).decode('utf-8')
    
    return img_base64
    

def visualize_semester_chart_agent():
    prompt = load_prompt_template('prompts/visualize_semester_chart.yaml')
    llm   = ChatOpenAI(model="gpt-4o", temperature=0)
    tools = [python_repl_tool]
    agent = create_tool_calling_agent(llm=llm,tools=tools,prompt=prompt)
    agent_executor = AgentExecutor.from_agent_and_tools(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=1
    )
    return agent_executor


def visualize_ratio_category_agent():
    prompt = load_prompt_template('prompts/visualize_ratio_category.yaml')
    llm   = ChatOpenAI(model="gpt-4o", temperature=0)
    tools = [python_repl_tool]
    agent = create_tool_calling_agent(llm=llm,tools=tools,prompt=prompt)
    agent_executor = AgentExecutor.from_agent_and_tools(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=1
    )
    return agent_executor