from analyst_agent.react.code_executor_node import DataFrameCodeExecutorNode, ChartCodeExecutorNode
from analyst_agent.react.router_node import RouterNode
from analyst_agent.react.code_generator_node import DataFrameCodeGeneratorNode, ChartCodeGeneratorNode
from analyst_agent.react.state import AgentContextState, DataFrameState, ChartState
from analyst_agent.react.graph_executor_node import DataFrameAgentExecutorNode, ChartAgentExecutorNode
from typing import Dict, Any
from langgraph.graph import StateGraph, END, START
from langgraph.graph.state import CompiledStateGraph
from langgraph.checkpoint.memory import MemorySaver  
from queue import Queue


def chart_code_react_agent(verbose: bool = False, track_time: bool = False, queue: Queue=None) -> CompiledStateGraph:
    chart_code_generator_node = ChartCodeGeneratorNode(verbose=verbose, track_time=track_time, queue=queue)
    chart_code_executor_node = ChartCodeExecutorNode(verbose=verbose, track_time=track_time, queue=queue)
    
    chart_code_agent_workflow = StateGraph(ChartState)
    chart_code_agent_workflow.add_node('chart_code_generator', chart_code_generator_node)
    chart_code_agent_workflow.add_node('chart_code_executor', chart_code_executor_node)
    chart_code_agent_workflow.add_edge(START, 'chart_code_generator')
    chart_code_agent_workflow.add_edge('chart_code_generator', 'chart_code_executor')
    chart_code_agent_workflow.add_conditional_edges('chart_code_executor', check_code_validity, {"finish": END, "regenerate": 'chart_code_generator'})
    chart_memory = MemorySaver()
    return chart_code_agent_workflow.compile(checkpointer=chart_memory)

def df_code_react_agent(verbose: bool = False, track_time: bool = False, queue: Queue=None) -> CompiledStateGraph:
    dataframe_code_generator_node = DataFrameCodeGeneratorNode(verbose=verbose, track_time=track_time, queue=queue)
    dataframe_code_executor_node = DataFrameCodeExecutorNode(verbose=verbose, track_time=track_time, queue=queue)
    
    dataframe_code_agent_workflow = StateGraph(DataFrameState)
    dataframe_code_agent_workflow.add_node('dataframe_code_generator', dataframe_code_generator_node)
    dataframe_code_agent_workflow.add_node('dataframe_code_executor', dataframe_code_executor_node)
    dataframe_code_agent_workflow.add_edge(START, 'dataframe_code_generator')
    dataframe_code_agent_workflow.add_edge('dataframe_code_generator', 'dataframe_code_executor')
    dataframe_code_agent_workflow.add_conditional_edges('dataframe_code_executor', check_code_validity, {"finish": END, "regenerate": 'dataframe_code_generator'})
    dataframe_memory = MemorySaver()
    return dataframe_code_agent_workflow.compile(checkpointer=dataframe_memory)


def react_code_agent(verbose: bool = False, track_time: bool = False, queue: Queue=None) -> CompiledStateGraph:
    router_node = RouterNode(verbose=verbose, track_time=track_time, queue=queue)
    dataframe_code_agent = DataFrameAgentExecutorNode(verbose=verbose, track_time=track_time, queue=queue)
    chart_code_agent = ChartAgentExecutorNode(verbose=verbose, track_time=track_time, queue=queue)
    
    react_code_agent_workflow = StateGraph(AgentContextState)
    react_code_agent_workflow.add_node('router', router_node)
    react_code_agent_workflow.add_node('dataframe_code_agent', dataframe_code_agent)
    react_code_agent_workflow.add_node('chart_code_agent', chart_code_agent)

    react_code_agent_workflow.add_conditional_edges('router', check_next_action, {"to_gen_df": 'dataframe_code_agent', "to_gen_chart": 'chart_code_agent', "finish": END})
    react_code_agent_workflow.add_edge('dataframe_code_agent', 'router')
    react_code_agent_workflow.add_edge('chart_code_agent', 'router')
    react_code_agent_workflow.set_entry_point('router')
    
    react_memory = MemorySaver()
    return react_code_agent_workflow.compile(checkpointer=react_memory)




def check_code_validity (state: Dict[str, Any]) -> str:
    print("---CODE VALIDITY CHECKER---")
    code_error = state.get("last_error", "")

    if code_error == "":
        print ("---CONTINUE---")
        return "finish"
    else:
        print ("---[ERROR] CODE REWRITE---")
        return "regenerate"


def check_next_action(state: Dict[str, Any]) -> str:
    '["to_gen_df", "to_gen_chart", "finish"]'
    print("---NEXT ACTION CHECKER---")
    next_action = state.get("next_action", "")
    if next_action == "to_gen_df":
        return "to_gen_df"
    elif next_action == "to_gen_chart":
        return "to_gen_chart"
    elif next_action == "finish":
        print("---CODE AGENT FINISH---")
        return "finish"
        