from fastapi import APIRouter, UploadFile, File, HTTPException, WebSocket, WebSocketDisconnect
from parser.graph import transcript_extract_graph
from pydantic    import BaseModel
import os
import shutil
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
        while True:
            # Keep the connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(session_id)

@router.post("/upload/{session_id}")
async def parse_pdf(session_id: str):
    
    '''
    Accepts a PDF-file upload, processes it through the LangGraph pipeline,
    and returns the extracted final result as Json(dict)
    '''
    session_dir = CLIENT_DATA_DIR / session_id
    if not session_dir.exists() or not any(session_dir.iterdir()):
        raise HTTPException(status_code=404, detail="No file found for this session.")

    # Find the first PDF file in the directory
    pdf_path = next((p for p in session_dir.glob("*.pdf")), None)

    if not pdf_path:
        raise HTTPException(status_code=400, detail="No PDF file found in the session directory.")

    try:
        q = Queue()
        graph = transcript_extract_graph(queue=q)
        config = {"configurable": {"thread_id": session_id}}
        input_state = {'filepath': str(pdf_path)}
        
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

        thread.join()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF processing failed: {e}")

    final_text = result_state.get("final_result") if isinstance(result_state, dict) else None

    if not final_text:
        raise HTTPException(status_code=500, detail="PDF processing failed to produce a result.")
    
    return PDFProcessResponse(final_result=final_text)

@router.post("/analyze/{session_id}")
def analyze_transcript(transcript: Transcript, session_id: str):
    """
    Analyzes the transcript and returns a report and visualizations.
    """
    return run_analysis(transcript.transcript, session_id)

