from langgraph.graph import StateGraph, END, START
from langgraph.graph.state import CompiledStateGraph
from langgraph.checkpoint.memory import MemorySaver  
from queue import Queue
from langchain_core.runnables import RunnableConfig  
from base_node.base import BaseNode
from base_node.env_model import Env

from analyst_agent.state import ReportState
from analyst_agent.transcript_analyst_node import TranscriptAnalystNode
from analyst_agent.react_code_agent import react_code_agent, AgentContextState
from analyst_agent.metric_insight_node import MetricInsightNode
from analyst_agent.analysis_planner_node import AnalysisPlannerNode
from analyst_agent.data_extractor_node import DataExtractorNode


class MetricInsightSchedulingNode(BaseNode):
    def __init__(self, verbose=False, track_time=False, queue: Queue=None, env: Env=None):
        super().__init__(verbose=verbose, track_time=track_time, queue=queue, env=env)
        self.verbose = verbose
        self.track_time = track_time
        self.queue = queue
        self.env = env
        
    def run(self, state: ReportState):
        react_code_agent_graph = react_code_agent(verbose=self.verbose, track_time=self.track_time, queue=self.queue, env=self.env)
        report_plan = []
        config = RunnableConfig(thread_id=state['run_id'], max_iterations=30) 
        schema_explanations = '''
            - id : Stable indentifier
            - rationalbe: Reason for extracting this metric
            - compute_hint: Short hint for DF/Chart generation
            - chart_type: One of ['line','bar','stacked_bar','scatter','pie','none']
            - produces: One of ['table','chart','metric']
            - tags: List of tags
            - semantic_course_names: List of course names

            <instruction>
            1. semantic_course_names이 존재한다면, 이 과목만 활용하여 dataframe을 추출해야합니다.
            2. compute_hint, chart_type을 참고하여 dataframe과 chart를 생성해야합니다.
            3. produces가 'table'이면 dataframe만 생성하면 됩니다.
            </instruction>
            '''
        
        note = '''
        <attention>
        1. 차트를 생성할 때 이수 과목을 원문 그대로 반드시 한글로 작성해야 한다.
        2. 평균 값을 계산하지 않고, 데이터를 활용하여 csv, chart를 생성해야 한다.
           단 , metric_spec의 produces가 metric인 경우를 제외한다.
        </attention>
        '''
        
        for metric_spec in state['metric_plan']:
            input_metric_dict = metric_spec.model_dump(exclude={"extraction_mode", "extraction_query"})
            
            DEFAULT_AGENT_CONTEXT_STATE = {
            'user_query': '',
            'dataset': '',
            'run_id':'',
            'attempts': {},
            'errors': [],
            'chart_name':'',
            'chart_desc':'',
            'chart_code': '',
            'img_path': '',
            'csv_path':'',
            'df_code': '',
            'df_name':'',
            'df_desc':'',
            'df_meta':{},
            'previous_node':'_START_',
            'next_action': '',
            'cost' : 0.0,
            }
            user_input = {
                'user_query': input_metric_dict,
                'schema_explanations': schema_explanations,
                'note': note,
            }
            input_values = {
                **DEFAULT_AGENT_CONTEXT_STATE,
                'user_query': user_input,
                'run_id':state['run_id'],
                'dataset': state['dataset'],
            }
            react_code_agent_result : AgentContextState = react_code_agent_graph.invoke(
            input=input_values,
            config=config
            )
            csv_path = react_code_agent_result['csv_path']
            chart_path = react_code_agent_result['img_path']
            status = react_code_agent_result['status']
            if status.status != "normal":
                state['cost'] += react_code_agent_result['cost']
                
            state['cost'] += react_code_agent_result['cost']

            input_insight = {
                'csv_path' : csv_path,
                'chart_path': chart_path,
                'metric_spec': metric_spec,
                'analyst': state['analyst'],
                'run_id': state['run_id'],
                'cost' : 0.0,
                'message': status.message,
            }

            metric_insight_node = MetricInsightNode(verbose=self.verbose, track_time=self.track_time, queue=self.queue, env=self.env)
            metric_insight_result = metric_insight_node(input_insight)
            report_plan.append(metric_insight_result['metric_insight'])
            state['cost'] += metric_insight_result['cost']
        state['report_plan'] = report_plan
        return state

def transcript_analyst_graph(verbose: bool = False, track_time: bool = False, queue: Queue=None, env: Env=None) -> CompiledStateGraph:
    analysis_planner_node = AnalysisPlannerNode(verbose=verbose, track_time=track_time, queue=queue, env=env)
    data_extractor_node = DataExtractorNode(verbose=verbose, track_time=track_time, queue=queue, env=env)
    metric_insight_scheduling_node = MetricInsightSchedulingNode(verbose=verbose, track_time=track_time, queue=queue, env=env)
    transcript_analyst_node = TranscriptAnalystNode(verbose=verbose, track_time=track_time, queue=queue, env=env)
    
    report_graph = StateGraph(ReportState)
    report_graph.add_node("analysis_planner", analysis_planner_node)
    report_graph.add_node("data_extractor", data_extractor_node)
    report_graph.add_node("metric_insight_scheduling", metric_insight_scheduling_node)
    report_graph.add_node("transcript_analyst", transcript_analyst_node)
    
    report_graph.add_edge(START, "analysis_planner")
    report_graph.add_edge("analysis_planner", "data_extractor")
    report_graph.add_edge("data_extractor", "metric_insight_scheduling")
    report_graph.add_edge("react_code_agent", "transcript_analyst")
    report_graph.add_edge("transcript_analyst", END)
    memory = MemorySaver()
    return report_graph.compile(checkpointer=memory)