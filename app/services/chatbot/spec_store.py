from typing import Dict

class SpecStore:
    def __init__(self):
        self._store: Dict[str, dict] = {}

    def set_spec(self, session_id: str, spec: dict):
        self._store[session_id] = spec

    def get_spec(self, session_id: str) -> dict:
        return self._store.get(session_id, {})

spec_store = SpecStore()
