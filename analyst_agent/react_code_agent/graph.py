from analyst_agent.react_code_agent.code_executor_node import DataFrameCodeExecutorNode, ChartCodeExecutorNode
from analyst_agent.react_code_agent.router_node import RouterNode
from analyst_agent.react_code_agent.code_generator_node import DataFrameCodeGeneratorNode, ChartCodeGeneratorNode
from analyst_agent.react_code_agent.state import AgentContextState, DataFrameState, ChartState, Status
from typing import Dict, Any
from langgraph.graph import StateGraph, END, START
from langgraph.graph.state import CompiledStateGraph
from langgraph.checkpoint.memory import MemorySaver  
from queue import Queue
from langchain_core.runnables import RunnableConfig  
from base_node.base import BaseNode
from base_node.env_model import Env


#TODO bring csv file path and create methods to read csv file in codeexecutornode.
class ChartAgentExecutorNode(BaseNode):
    '''
    차트 생성 agent를 실행시키는 node.
    '''
    def __init__(self, verbose=False, env: Env=None, queue: Queue=None, **kwargs):
        super().__init__(verbose=verbose, env=env, queue=queue, **kwargs)

    
    def run(self, state: AgentContextState):
        config = RunnableConfig(recursion_limit=5) 
        chart_graph = chart_code_react_agent(queue=self.queue, env=self.env)

        user_query = state['user_query']
        df_name = state['df_name']
        df_desc = state['df_desc']
        df_meta = state['df_meta']
        df_code = state['df_code']
        chart_name = state['chart_name']
        chart_desc = state['chart_desc']
        csv_path = state['csv_path']
        run_id = state['run_id']
        cost = state['cost']
        

        input_values = {
            'user_query' : user_query, 
            'df_name': df_name,
            'df_desc': df_desc,
            'chart_name': chart_name,
            'chart_desc': chart_desc,
            'csv_path': csv_path,
            'run_id': run_id,
            'df_meta': df_meta,
            'df_code': df_code,
            'chart_code': '',
            'chart_intent': {},
            'stdout': '',
            'stderr': '',
            'error_logs': '',
            'errors': [],
            'attempts': 0,
            'debug_font': {},
            'img_path': '',
            'status': Status(status="normal", message="Everything is running smoothly."),
            'cost': cost,
        }

        self.logger.info("Invoking chart_code_react_agent …")
        self.logger.debug(f"chart_code_react_agent input preview: {input_values}")

        result : ChartState = chart_graph.invoke(
            input=input_values,
            config=config
            )
        img_path = result['img_path']
        chart_desc = result['chart_desc']
        chart_name = result['chart_name']
        state['img_path'] = img_path
        state['chart_desc'] = chart_desc
        state['chart_name'] = chart_name
        state['previous_node'] = "chart_exec"
        state['status'] = result['status']
        state['cost'] = result['cost']
        return state


class DataFrameAgentExecutorNode(BaseNode):
    '''
    차트 생성 agent를 실행시키는 node.
    '''
    def __init__(self, verbose=False, env: Env=None, queue: Queue=None, **kwargs):
        super().__init__(verbose=verbose, env=env, queue=queue, **kwargs)

    #TODO bring csv file path and create methods to read csv file in codeexecutornode.
    def run(self, state: AgentContextState):
        
        config = RunnableConfig(recursion_limit=5) 
        df_graph = df_code_react_agent(queue=self.queue, env=self.env)

        DEFAULT_DATAFRAME_STATE = {
            "user_query": "",
            "run_id": "",
            "dataset": "",
            "df_code": "",
            "df_name": "",
            "df_desc": "",
            "df_handle": [],
            "df_meta": {},
            "csv_path": "",
            "stdout": "",
            "stderr": "",
            "attempts": 0,
            "error_log": "",
            "errors": [],
            "status": Status(status="normal", message="Everything is running smoothly."),
            "cost": 0.0,
        }
        input_values = {
            **DEFAULT_DATAFRAME_STATE,
            "user_query": state["user_query"],
            "dataset": state["dataset"],
            "df_name": state["df_name"],
            "df_code": state["df_code"],
            "df_desc": state["df_desc"],
            "error_log": "",
            "run_id": state["run_id"],
            "cost": state["cost"],
        }
        result : DataFrameState = df_graph.invoke(
            input=input_values,
            config=config
            )
        ''' output format
        df_code: str = Field(..., description="Python code to generate the DataFrame")
        df_name: str = Field(..., description="DataFrame name")
        df_desc: str = Field(..., description="DataFrame description")
        '''
        state['df_code'] = result['df_code']
        state['df_name'] = result['df_name']
        state['df_desc'] = result['df_desc']
        state['csv_path'] = result['csv_path']
        state['df_meta'] = result['df_meta']
        state['previous_node'] = "df_exec"
        state['status'] = result['status']
        state['cost'] = result['cost']
        return state

def chart_code_react_agent(verbose: bool = False, track_time: bool = False, queue: Queue=None, env: Env=None) -> CompiledStateGraph:
    chart_code_generator_node = ChartCodeGeneratorNode(verbose=verbose, track_time=track_time, queue=queue, env=env)
    chart_code_executor_node = ChartCodeExecutorNode(verbose=verbose, track_time=track_time, queue=queue, env=env)
    
    chart_code_agent_workflow = StateGraph(ChartState)
    chart_code_agent_workflow.add_node('chart_code_generator', chart_code_generator_node)
    chart_code_agent_workflow.add_node('chart_code_executor', chart_code_executor_node)
    chart_code_agent_workflow.add_edge(START, 'chart_code_generator')
    chart_code_agent_workflow.add_edge('chart_code_generator', 'chart_code_executor')
    chart_code_agent_workflow.add_conditional_edges('chart_code_executor', check_code_validity, {"finish": END, "regenerate": 'chart_code_generator'})
    chart_memory = MemorySaver()
    return chart_code_agent_workflow.compile(checkpointer=chart_memory)

def df_code_react_agent(verbose: bool = False, track_time: bool = False, queue: Queue=None, env: Env=None) -> CompiledStateGraph:
    dataframe_code_generator_node = DataFrameCodeGeneratorNode(verbose=verbose, track_time=track_time, queue=queue, env=env)
    dataframe_code_executor_node = DataFrameCodeExecutorNode(verbose=verbose, track_time=track_time, queue=queue, env=env)
    
    dataframe_code_agent_workflow = StateGraph(DataFrameState)
    dataframe_code_agent_workflow.add_node('dataframe_code_generator', dataframe_code_generator_node)
    dataframe_code_agent_workflow.add_node('dataframe_code_executor', dataframe_code_executor_node)
    dataframe_code_agent_workflow.add_edge(START, 'dataframe_code_generator')
    dataframe_code_agent_workflow.add_edge('dataframe_code_generator', 'dataframe_code_executor')
    dataframe_code_agent_workflow.add_conditional_edges('dataframe_code_executor', check_code_validity, {"finish": END, "regenerate": 'dataframe_code_generator'})
    dataframe_memory = MemorySaver()
    return dataframe_code_agent_workflow.compile(checkpointer=dataframe_memory)


def react_code_agent(verbose: bool = False, track_time: bool = False, queue: Queue=None, env: Env=None) -> CompiledStateGraph:
    router_node = RouterNode(verbose=verbose, track_time=track_time, queue=queue, env=env)
    dataframe_code_agent = DataFrameAgentExecutorNode(verbose=verbose, track_time=track_time, queue=queue, env=env)
    chart_code_agent = ChartAgentExecutorNode(verbose=verbose, track_time=track_time, queue=queue, env=env)
    
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
    code_error = state.get("error_log", "")

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