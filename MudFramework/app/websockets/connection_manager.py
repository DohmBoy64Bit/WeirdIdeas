from typing import List, Dict
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        # Store active connections: player_id -> WebSocket
        self.active_connections: Dict[int, WebSocket] = {}

    async def connect(self, websocket: WebSocket, player_id: int):
        await websocket.accept()
        self.active_connections[player_id] = websocket

    def disconnect(self, player_id: int):
        if player_id in self.active_connections:
            del self.active_connections[player_id]

    async def send_personal_message(self, message: dict, player_id: int):
        if player_id in self.active_connections:
            await self.active_connections[player_id].send_json(message)

    async def broadcast(self, message: dict):
        for connection in self.active_connections.values():
            await connection.send_json(message)

manager = ConnectionManager()
