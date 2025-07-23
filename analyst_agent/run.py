from analyst_agent.agent import visualize_semester_chart_agent, visualize_ratio_category_agent
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from .utils import load_prompt_template
from typing import Union, Dict
import json


def run_analysis(transcript: Union[str, Dict]):
    """
    Runs the analysis on the transcript.
    """
    if isinstance(transcript, Dict):
        text_for_llm = json.dumps(transcript, ensure_ascii=False, indent=2)
    else :
        text_for_llm = transcript
    
    # Generate visualizations
    semester_chart_agent = visualize_semester_chart_agent()
    ratio_category_agent = visualize_ratio_category_agent()

    semester_chart = semester_chart_agent.invoke({"transcript_json": text_for_llm})
    ratio_category_chart = ratio_category_agent.invoke({"transcript_json": text_for_llm})

    return {
        "report": transcript,
        "visualizations": [
            semester_chart['output'],
            ratio_category_chart['output']
        ],
    }
