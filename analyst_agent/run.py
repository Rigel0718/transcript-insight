from analyst_agent.agent import visualize_semester_chart_agent, visualize_ratio_category_agent
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from utils import load_prompt_template

def run_analysis(transcript: str):
    """
    Runs the analysis on the transcript.
    """

    # Generate visualizations
    semester_chart_agent = visualize_semester_chart_agent()
    ratio_category_agent = visualize_ratio_category_agent()

    semester_chart = semester_chart_agent.invoke({"input": transcript})
    ratio_category_chart = ratio_category_agent.invoke({"input": transcript})

    return {
        "report": transcript,
        "visualizations": [
            semester_chart['output'],
            ratio_category_chart['output']
        ],
    }
