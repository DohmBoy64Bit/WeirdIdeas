import logging
from typing import Dict, List
from fastapi import WebSocket

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manage WebSocket connections grouped by lobby_id."""

    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, lobby_id: str, websocket: WebSocket):
        logger.debug("connect attempt lobby=%s conn=%r", lobby_id, websocket)
        await websocket.accept()
        self.active_connections.setdefault(lobby_id, []).append(websocket)
        conns = self.active_connections.get(lobby_id, [])
        logger.debug("connected: lobby=%s total_conns=%d", lobby_id, len(conns))

    def disconnect(self, lobby_id: str, websocket: WebSocket):
        logger.debug("disconnect attempt lobby=%s conn=%r", lobby_id, websocket)
        conns = self.active_connections.get(lobby_id) or []
        if websocket in conns:
            conns.remove(websocket)
        if not conns:
            self.active_connections.pop(lobby_id, None)
            logger.debug("lobby %s now has 0 conns, removed", lobby_id)
        else:
            logger.debug("lobby %s now has %d conns", lobby_id, len(conns))

    async def broadcast(self, lobby_id: str, message: dict):
        conns = list(self.active_connections.get(lobby_id, []))
        logger.debug("broadcast to lobby %s: type=%s conns=%d", lobby_id, message.get('type'), len(conns))
        for ws in conns:
            try:
                logger.debug("sending to conn %r type=%s", ws, message.get('type'))
                await ws.send_json(message)
                logger.debug("sent to conn %r", ws)
            except Exception as e:
                logger.exception("send error to %r: %s", ws, e)
                # on error remove connection
                try:
                    await ws.close()
                except Exception:
                    pass
                self.disconnect(lobby_id, ws)


# Singleton manager instance used by ws and services
manager = ConnectionManager()