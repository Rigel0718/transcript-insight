from .analyst_nodes import CodeExecutorNode, Text2ChartNode, DataFrameExtractorNode, QueryReWrite
from .state import Text2ChartState
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph
import os
from langgraph.checkpoint.memory import MemorySaver  
from queue import Queue

def text2chart_graph(queue: Queue=None) -> CompiledStateGraph:
    query_rewrite_node = QueryReWrite(verbose=True, queue=queue)
    dataframe_extractor_node = DataFrameExtractorNode(verbose=True, queue=queue)
    text2chart_node = Text2ChartNode(verbose=True, queue=queue)
    code_executor_node = CodeExecutorNode(verbose=True, queue=queue)
    
    text2chart_workflow = StateGraph(Text2ChartState)
    text2chart_workflow.add_node('query_rewrite', query_rewrite_node)
    text2chart_workflow.add_node('dataframe_extractor', dataframe_extractor_node)
    text2chart_workflow.add_node('text2chart', text2chart_node)
    text2chart_workflow.add_node('code_executor', code_executor_node)
    text2chart_workflow.add_edge('query_rewrite', 'dataframe_extractor')
    text2chart_workflow.add_edge('dataframe_extractor', 'text2chart')
    text2chart_workflow.add_edge('text2chart', 'code_executor')
    text2chart_workflow.add_conditional_edges('code_executor', check_code_validity , {"continue": 'text2chart', "rewrite": 'code_executor'})
    
    text2chart_workflow.set_entry_point('query_rewrite')
    text2chart_workflow.set_finish_point('code_executor')
    return text2chart_workflow.compile(checkpointer=MemorySaver())


def check_code_validity (state: Text2ChartState):
    print("---CODE VALIDITY CHECKER---")
    code_error = state["code_err"]

    if code_error == "None":
        print ("---CONTINUE---")
        return "continue"
    else:
        print ("---[ERROR] CODE REWRITE---")
        return "rewrite"