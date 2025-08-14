from analyst_agent.react.state import DataFrameState, ChartState, AgentContextState
from analyst_agent.react.base import BaseNode
from analyst_agent.react.graph import chart_code_react_agent, df_code_react_agent
from langchain_core.runnables import RunnableConfig  
from queue import Queue

#TODO bring csv file path and create methods to read csv file in codeexecutornode.
class ChartAgentExecutorNode(BaseNode):
    '''
    차트 생성 agent를 실행시키는 node.
    '''
    def __init__(self, verbose=False, queue: Queue=None, **kwargs):
        super().__init__(verbose=verbose, queue=queue, **kwargs)

    
    def run(self, state: AgentContextState):
        config = RunnableConfig(recursion_limit=5) 
        chart_graph = chart_code_react_agent(queue=self.queue)
        result : ChartState = chart_graph.invoke(
            input={
                'user_query' : state['user_query'], 
                'current_dataframe_informs': state['current_dataframe_informs'],
                'current_chart_informs': state['current_chart_informs'],
            },
            config=config
            )
        return {"chart_state": result}


class DataFrameAgentExecutorNode(BaseNode):
    '''
    차트 생성 agent를 실행시키는 node.
    '''
    def __init__(self, verbose=False, queue: Queue=None, **kwargs):
        super().__init__(verbose=verbose, queue=queue, **kwargs)

    #TODO bring csv file path and create methods to read csv file in codeexecutornode.
    def run(self, state: AgentContextState):
        
        config = RunnableConfig(recursion_limit=5) 
        df_graph = df_code_react_agent(queue=self.queue)
        result : DataFrameState = df_graph.invoke(
            input={
                'user_query' : state['user_query'], 
                'dataset': state['dataset'],
                'error_log': state['last_error']
            },
            config=config
            )
        state['current_dataframe_informs'] = result['df_info']
        return state