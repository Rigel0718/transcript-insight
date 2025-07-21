from langchain.tools import tool
from typing import Annotated
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_openai import ChatOpenAI
from analyst_agent.utils import load_prompt_template
import io
import sys
from contextlib import redirect_stdout
import matplotlib.pyplot as plt

@tool
def python_repl_tool(
    code: Annotated[str, "The python code to execute to generate your chart."],
):
    """
    Use this tool to execute Python code. Automatically detects whether matplotlib is used.
    Supports both visualization and regular code. Stdout is captured and returned.
    """
    plt.clf()
    
    f = io.StringIO()
    with redirect_stdout(f):
        try:
            exec(code, globals())
        except Exception as e:
            return f"Failed to execute. Error: {repr(e)}\n{f.getvalue()}"
    
    return f.getvalue()
    

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
