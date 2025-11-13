from app.services.chatbot.spec_store import spec_store
from fastapi import APIRouter

spec_router = APIRouter()

@spec_router.post("/spec/{session_id}")
def save_spec(session_id: str, spec: dict):
    spec_store.set_spec(session_id, spec)
    return {"status": "ok"}

@spec_router.get("/spec/{session_id}")
def get_spec(session_id: str):
    return spec_store.get_spec(session_id)