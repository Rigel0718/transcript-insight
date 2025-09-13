from fastapi import WebSocket
from typing import Dict
import logging

class ConnectionManager:
    '''
    Manage multiple WebSocket clients using session_id as the key.
    
    - connect(): Accepts a new WebSocket and registers it with the given session_id.
    - disconnect(): Removes the WebSocket associated with the session_id.
    - send_to(): Sends a message to the specific WebSocket associated with the session_id.
    '''
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket

    def disconnect(self, session_id: str):
        self.active_connections.pop(session_id, None)

    async def send_to(self, session_id: str, message: str) -> bool:
        websocket = self.active_connections.get(session_id)
        if not websocket:
            return False
        try:
            await websocket.send_text(message)
            return True
        except Exception as e:
            logging.getLogger("ConnectionManager").warning(
                f"send_to failed for {session_id}: {e}. Disconnecting.")
            self.disconnect(session_id)
            return False

manager = ConnectionManager()
