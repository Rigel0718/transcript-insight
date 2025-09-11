from fastapi import APIRouter, UploadFile, File, HTTPException, WebSocket, WebSocketDisconnect
from parser.graph import transcript_extract_graph
from pydantic    import BaseModel
import os
import shutil
import tempfile
from analyst_agent import transcript_analyst_graph, AnalysisSpec, ReportState
from typing import Union, Dict, Any, Optional
import asyncio
from queue import Queue
import json
from threading import Thread
from .connection_manager import manager
from pathlib import Path
from base_node import Env, RunLogger
from datetime import datetime
from langchain_core.runnables import RunnableConfig  



router = APIRouter()

CLIENT_DATA_DIR = Path("test_data")

class PDFProcessResponse(BaseModel):
    final_result: Union[str, Dict]


class AnalyzeRequest(BaseModel):
    transcript: Dict[str, Any]
    analyst: AnalysisSpec
    url : Optional[str] = None

class Report(BaseModel):
    report: str

@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await manager.connect(websocket, session_id)
    try:
        async for _ in websocket.iter_text():
            pass
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(session_id)



@router.post("/upload/{session_id}")
async def parse_pdf(session_id: str, file: UploadFile = File(...)):
    
    '''
    Accepts a PDF-file upload, processes it through the LangGraph pipeline,
    and returns the extracted final result as Json(dict)
    '''

    # Validate file type (must be PDF).
    file_name = file.filename or 'uploaded_file'
    file_suffix = os.path.splitext(file_name)[1].lower()

    if file_suffix != '.pdf' or file.content_type not in ('application/pdf', 'application/octet-stream'):
        raise HTTPException(status_code=400, detail="Invalid file type, Please upload a PDF file")
    
    # Save the uploaded file to a secure temporary dir.
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, f'{session_id}.pdf')

    try:
        file_contents = await file.read()
        with open(temp_path, 'wb') as f:
            f.write(file_contents)

    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"Fail store the file: {e}")
    
    finally:
        await file.close()

    try:
        q = Queue()
        graph = transcript_extract_graph(queue=q)
        config = {"configurable": {"thread_id": str(session_id)}}
        input_state = {'filepath': temp_path}
        
        result_state = {}
        def run_graph():
            result = graph.invoke(input=input_state, config=config)
            result_state.update(result)

        thread = Thread(target=run_graph)
        thread.start()

        while thread.is_alive() or not q.empty():
            if not q.empty():
                event = q.get()
                await manager.send_to(session_id, json.dumps(event))
            else:
                await asyncio.sleep(0.1)
        
        await manager.send_to(session_id, json.dumps({"event": "eof"}))
        await asyncio.sleep(0.1)
        thread.join()

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

    final_text = result_state.get("final_result", None)
    if not final_text:
        raise HTTPException(status_code=500, detail="No final result produced by the pipeline.")

    return PDFProcessResponse(final_result=final_text)
    

@router.post("/analyze/{session_id}")
async def analyze_transcript(session_id: str, req: AnalyzeRequest):
    """
    Analyzes the transcript report with Table and Chart.
    """
    transcript = req.transcript
    analyst = req.analyst
    

    
    run_id = datetime.now().strftime("%Y-%m-%d-%H-%M%S")
    logger = RunLogger()
    env = Env(
    work_dir=CLIENT_DATA_DIR,
    user_id=session_id,
    run_logger=logger,
    url=req.url,
    )
    q = Queue()
    graph = transcript_analyst_graph(queue=q, verbose=True, env=env, track_time=True)
    config = RunnableConfig(thread_id=str(session_id), max_iterations=40)
    text_transcript = json.dumps(transcript, ensure_ascii=False, indent=2)
    input_state = ReportState(
        dataset=text_transcript,
        user_query='',
        analyst=analyst,
        run_id=run_id,
    )

    result_state = {}
    def run_graph():
        result = graph.invoke(input=input_state, config=config)
        result_state.update(result)

    thread = Thread(target=run_graph)
    thread.start()

    while thread.is_alive() or not q.empty():
        if not q.empty():
            event = q.get()
            await manager.send_to(session_id, json.dumps(event))
        else:
            await asyncio.sleep(0.1)
    
    await manager.send_to(session_id, json.dumps({"event": "eof"}))
    await asyncio.sleep(0.1)
    thread.join()
            
    report = result_state.get("report", None)
    if not report:
        raise HTTPException(status_code=500, detail="No final result produced by the pipeline.")

    return Report(report=report)

