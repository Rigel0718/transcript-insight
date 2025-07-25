from fastapi import APIRouter, UploadFile, File, HTTPException, WebSocket, WebSocketDisconnect
from parser.graph import transcript_extract_graph
from pydantic    import BaseModel
import os
import shutil
import tempfile
from analyst_agent.run import run_analysis
from typing import Union, Dict
import asyncio
from queue import Queue
import json
from threading import Thread
from .connection_manager import manager
from pathlib import Path

router = APIRouter()

CLIENT_DATA_DIR = Path("client_data")

class PDFProcessResponse(BaseModel):
    final_result: Union[str, Dict]

class Transcript(BaseModel):
    transcript: Union[str, Dict]

@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await manager.connect(websocket, session_id)
    try:
        data = await websocket.receive_text()
    except WebSocketDisconnect:
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
    temp_user_id = session_id
    temp_path = os.path.join(temp_dir, f'{temp_user_id}.pdf')

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
        config = {"configurable": {"thread_id": str(temp_user_id)}}
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
                await manager.send_to(temp_user_id, json.dumps(event))
            else:
                await asyncio.sleep(0.1)
        
        await manager.send_to(temp_user_id, json.dumps({"event": "eof"}))
        await asyncio.sleep(0.1)
        thread.join()

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

    final_text = result_state.get("final_result", None)
    if not final_text:
        raise HTTPException(status_code=500, detail="No final result produced by the pipeline.")

    return PDFProcessResponse(final_result=final_text)
    

@router.post("/analyze/{session_id}")
def analyze_transcript(transcript: Transcript, session_id: str):
    """
    Analyzes the transcript and returns a report and visualizations.
    """
    return run_analysis(transcript.transcript, session_id)

