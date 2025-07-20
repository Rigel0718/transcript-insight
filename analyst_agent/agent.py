from langchain.tools import tool
from langchain_experimental.utilities import PythonREPL
from typing import Annotated
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_openai import ChatOpenAI
from utils import load_prompt_template

@tool
def python_repl_tool(
    code: Annotated[str, "The python code to execute to generate your chart."],
):
    """Use this to execute python code. If you want to see the output of a value,
    you should print it out with `print(...)`. This is visible to the user."""
    result = ""
    print(code)
    
    try: 
        result = PythonREPL().run(code)
    except BaseException as e:
        print(f"Failed to execute. Error: {repr(e)}")
    finally:
        return result
    

def visualize_semester_chart_agent():
    prompt = load_prompt_template('prompts/semester_chart_visualize.yaml')
    llm   = ChatOpenAI(model="gpt-4o", temperature=0)
    tools = [python_repl_tool]
    agent = create_tool_calling_agent(llm=llm,tools=tools,prompt=prompt)
    agent_executor = AgentExecutor.from_agent_and_tools(
        agent=agent,
        tools=tools,
        verbos=True,
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
        verbos=True,
        handle_parsing_errors=True,
        max_iterations=1
    )
    return agent_executor