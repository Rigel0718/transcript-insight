from fastapi import APIRouter, UploadFile, File
from parser.graph import transcript_extract_graph

router = APIRouter()

@router.post("/upload/")
async def parse_pdf(file: UploadFile = File(...)):
    
    temp_path = f"/tmp/{file.filename}"
    with open(temp_path, "wb") as f:
        f.write(await file.read())

    
    result = transcript_extract_graph().invoke({"filepath": temp_path})
    return {"result": result["final_result"]}