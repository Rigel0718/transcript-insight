from langgraph.graph import StateGraph, END, START
from langgraph.graph.state import CompiledStateGraph
from langgraph.checkpoint.memory import MemorySaver  
from queue import Queue
from langchain_core.runnables import RunnableConfig  
from app.core.base import BaseNode
from app.core.env_model import Env

from app.analyst_agent.state import ReportState
from app.analyst_agent.transcript_analyst_node import TranscriptAnalystNode
from app.analyst_agent.react_code_agent import react_code_agent, AgentContextState
from app.analyst_agent.metric_insight_node import MetricInsightNode
from app.analyst_agent.analysis_planner_node import AnalysisPlannerNode
from app.analyst_agent.data_extractor_node import DataExtractorNode
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, Tuple


class MetricInsightSchedulingNode(BaseNode):
    def __init__(self, verbose=False, track_time=False, queue: Queue=None, env: Env=None):
        super().__init__(verbose=verbose, track_time=track_time, queue=queue, env=env)
        self.verbose = verbose
        self.track_time = track_time
        self.queue = queue
        self.env = env
        self.name = "Extracting Table and Chart."
        
    def run(self, state: ReportState):
        report_plan = []
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
        # Build inputs for each metric and launch the full pipeline (agent + insight) in parallel
        def build_agent_input(metric_spec) -> Dict[str, Any]:
            input_metric_dict = metric_spec.model_dump(exclude={"extraction_mode", "extraction_query"})
            default_state: Dict[str, Any] = {
                'user_query': '',
                'dataset': '',
                'run_id': '',
                'attempts': {},
                'errors': [],
                'chart_name': '',
                'chart_desc': '',
                'chart_code': '',
                'img_path': '',
                'csv_path': '',
                'df_code': '',
                'df_name': '',
                'df_desc': '',
                'df_meta': {},
                'previous_node': '_START_',
                'next_action': '',
                'cost': 0.0,
            }
            user_input = {
                'user_query': input_metric_dict,
                'schema_explanations': schema_explanations,
                'note': note,
            }
            metric_id = getattr(metric_spec, 'id', None) or input_metric_dict.get('id', '')
            # Initialize per-agent run_id with metric_id to avoid extra state fields
            return {
                **default_state,
                'user_query': user_input,
                'run_id': metric_id,
                'dataset': state['dataset'],
            }

        def run_full_pipeline_for_metric(metric_spec) -> Tuple[str, Dict[str, Any]]:
            """Run react_code_agent then MetricInsightNode for a single metric.
            Returns (metric_id, { 'insight': MetricInsightv2, 'cost': float })."""
            metric_id = getattr(metric_spec, 'id', None) or metric_spec.model_dump().get('id', '')
            # 1) Run code agent
            # Suppress per-metric event emission; keep logs intact
            graph = react_code_agent(verbose=self.verbose, track_time=self.track_time, queue=None, env=self.env)
            cfg = RunnableConfig(thread_id=f"{state['run_id']}:{metric_id}", max_iterations=30)
            inputs = build_agent_input(metric_spec)
            agent_result: AgentContextState = graph.invoke(input=inputs, config=cfg)
            agent_cost = float(agent_result.get('cost', 0.0)) if isinstance(agent_result, dict) else getattr(agent_result, 'cost', 0.0)

            # 2) Run insight node using agent outputs
            csv_path = agent_result.get('csv_path', '') if isinstance(agent_result, dict) else getattr(agent_result, 'csv_path', '')
            chart_path = agent_result.get('img_path', '') if isinstance(agent_result, dict) else getattr(agent_result, 'img_path', '')
            status = agent_result.get('status', {'status': 'unknown', 'message': ''}) if isinstance(agent_result, dict) else getattr(agent_result, 'status', {'status': 'unknown', 'message': ''})

            insight_input = {
                'csv_path': csv_path,
                'chart_path': chart_path,
                'metric_spec': metric_spec,
                'analyst': state['analyst'],
                'run_id': state['run_id'],
                'metric_id': metric_id,
                'cost': 0.0,
                'message': getattr(status, 'message', status.get('message', '') if isinstance(status, dict) else ''),
            }

            insight_node = MetricInsightNode(verbose=self.verbose, track_time=self.track_time, queue=None, env=self.env)
            insight_result = insight_node(insight_input)
            total_cost = agent_cost + float(insight_result.get('cost', 0.0))
            return metric_id, {
                'insight': insight_result.get('metric_insight'),
                'cost': total_cost,
            }

        metrics = state['metric_plan']
        total = len(metrics)
        max_workers = min(4, max(1, total))
        results_by_id: Dict[str, Dict[str, Any]] = {}

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_map = {executor.submit(run_full_pipeline_for_metric, spec): spec for spec in metrics}
            completed = 0
            for future in as_completed(future_map):
                spec = future_map[future]
                metric_id = getattr(spec, 'id', None) or spec.model_dump().get('id', '')
                try:
                    metric_id, result_bundle = future.result()
                    results_by_id[metric_id] = result_bundle
                except Exception as e:
                    # In case of failure, create a minimal error-like result
                    self.logger.error(f"react_code_agent failed for metric {metric_id}: {e}")
                    results_by_id[metric_id] = {'insight': None, 'cost': 0.0}
                finally:
                    completed += 1
                    self.emit_event("progress", completed=completed, total=total, metric_id=metric_id)

        for metric_spec in metrics:
            metric_id = getattr(metric_spec, 'id', None) or metric_spec.model_dump().get('id', '')
            bundle = results_by_id.get(metric_id, {})
            insight = bundle.get('insight')
            if insight is not None:
                report_plan.append(insight)
            state['cost'] += float(bundle.get('cost', 0.0))
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
    report_graph.add_edge("metric_insight_scheduling", "transcript_analyst")
    report_graph.add_edge("transcript_analyst", END)
    memory = MemorySaver()
    return report_graph.compile(checkpointer=memory)
