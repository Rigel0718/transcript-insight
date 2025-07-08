from fastapi import APIRouter, UploadFile, File, HTTPException
from parser.graph import transcript_extract_graph
from pydantic    import BaseModel
import os
import tempfile, uuid
import shutil

router = APIRouter()


class PDFProcessResponse(BaseModel):
    final_result: str

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
    temp_path = os.path.join(temp_dir, f'{uuid.uuid4()}.pdf')

    try:
        file_contents = await file.read()
        with open(temp_path, 'wb') as f:
            f.write(file_contents)

    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"Fail store the file: {e}")
    
    finally:
        await file.close()

    
    result = transcript_extract_graph().invoke({"filepath": temp_path})
    return {"result": result["final_result"]}