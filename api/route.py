from fastapi import APIRouter, UploadFile, File, HTTPException, WebSocket
from parser.graph import transcript_extract_graph
from pydantic    import BaseModel
import os
import tempfile, uuid
import shutil
from analyst_agent.run import run_analysis
from typing import Union, Dict
import asyncio
from queue import Queue
import json
from threading import Thread
from .connection_manager import manager

router = APIRouter()

class PDFProcessResponse(BaseModel):
    final_result: Union[str, Dict]

class Transcript(BaseModel):
    transcript: Union[str, Dict]

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except Exception as e:
        manager.disconnect(websocket)

@router.post("/upload/")
async def parse_pdf(file: UploadFile = File(...)):
    
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
    temp_user_id = uuid.uuid4()
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
                await manager.broadcast(json.dumps(event))
            else:
                await asyncio.sleep(0.1)
        
        await manager.broadcast(json.dumps({"event": "eof"}))

        thread.join()

    except Exception as e:  
        # if pipeline processing fails, clean up and return an error
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"PDF processing fail:{e}")
    
    if isinstance(result_state, dict):
        final_text=result_state.get('final_result')
    else:
        final_text = getattr(result_state,'final_resilt', None)
        if final_text is None and hasattr(result_state, '__getitem__'):
            final_text = result_state.get('final_result', None)

    if not final_text:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail="No final result produced by the pipeline.")
    
    shutil.rmtree(temp_dir, ignore_errors=True)
    
    return PDFProcessResponse(final_result=final_text)

@router.post("/analyze")
def analyze_transcript(transcript: Transcript):
    """
    Analyzes the transcript and returns a report and visualizations.
    """
    return run_analysis(transcript.transcript)

