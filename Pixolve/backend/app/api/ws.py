from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..services import auth_service, game_service
from .lobbies import _LOBBIES
from ..sockets.ws_manager import manager
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # Expect token and lobby id in query params: ?token=...&lobby=...
    token = websocket.query_params.get("token")
    lobby_id = websocket.query_params.get("lobby")
    if not token or not lobby_id:
        await websocket.close(code=1008)
        return

    user = auth_service.get_user_by_token(token)
    if not user:
        await websocket.close(code=1008)
        return

    if lobby_id not in _LOBBIES:
        await websocket.close(code=1008)
        return

    logger.debug("incoming connection: lobby=%s token=%s", lobby_id, token)
    await manager.connect(lobby_id, websocket)
    # Normalize username for logging (auth_service may return dict or model)
    if isinstance(user, dict):
        uname = user.get('username') or user.get('id')
    else:
        uname = getattr(user, 'username', getattr(user, 'id', None))
    logger.debug("new connection detail: lobby=%s user_obj=%r user_type=%s uname=%s", lobby_id, user, type(user), uname)
    # Notify current lobby state
    try:
        await manager.broadcast(lobby_id, {"type": "lobby_update", "data": {"players": [p.model_dump() for p in _LOBBIES[lobby_id].players]}})
        while True:
            try:
                logger.debug("awaiting message for lobby=%s user=%s", lobby_id, uname)
                data = await websocket.receive_json()
                logger.debug("received raw message from %s in lobby=%s: %r", uname, lobby_id, data)
            except Exception as e:
                # log and re-raise WebSocketDisconnect to trigger cleanup
                logger.exception("receive error for lobby=%s user=%s: %s", lobby_id, uname, e)
                raise
            typ = data.get("type")
            if typ == "submit_guess":
                # process guess server-side: compute correctness and award points
                payload = data.get("data", {})
                player_id = payload.get("player_id")
                text = payload.get("text")
                # delegate to game service to process
                try:
                    result = game_service.process_guess_for_lobby(lobby_id, player_id, text)
                    # log processing result and snapshot of scores before broadcasts
                    logger.debug("processed guess result for lobby=%s player=%s result=%r", lobby_id, player_id, result)
                    # broadcast guess_result to lobby
                    await manager.broadcast(lobby_id, {"type": "guess_result", "data": result})
                    # broadcast scoreboard update (current scores)
                    # find game for lobby
                    for g in game_service.GAMES.values():
                        if g.lobby_id == lobby_id:
                            runtime = game_service.RUNTIME.get(g.id, {})
                            scores = runtime.get("scores", {})
                            logger.debug("broadcasting scoreboard for lobby=%s scores=%r", lobby_id, scores)
                            await manager.broadcast(lobby_id, {"type": "scoreboard_update", "data": {"scores": scores}})
                            break
                except Exception as e:
                    await websocket.send_json({"type": "error", "data": str(e)})
            elif typ == "join_lobby":
                # simple broadcast for now
                await manager.broadcast(lobby_id, {"type": "lobby_update", "data": {"players": [p.model_dump() for p in _LOBBIES[lobby_id].players]}})
            elif typ == "player_ready":
                payload = data.get("data", {})
                pid = payload.get("player_id")
                ready = payload.get("ready", False)
                # update lobby player ready state
                for p in _LOBBIES[lobby_id].players:
                    if p.id == pid:
                        p.ready = ready
                await manager.broadcast(lobby_id, {"type": "lobby_update", "data": {"players": [p.model_dump() for p in _LOBBIES[lobby_id].players]}})
            elif typ == "chat":
                msg = data.get("data") or {}
                # attach server timestamp
                from datetime import datetime, timezone
                msg = {**msg, "ts": datetime.now(timezone.utc).isoformat()}
                logger.debug("received chat in lobby=%s msg=%r", lobby_id, msg)
                await manager.broadcast(lobby_id, {"type": "chat", "data": msg})
            elif typ == "start_game":
                # only allow host to start via websocket for convenience; find lobby and verify
                player = data.get("data", {}).get("player")
                if not player:
                    await websocket.send_json({"type": "error", "data": "missing_player"})
                    continue
                host_id = _LOBBIES[lobby_id].host_id
                if player.get("id") != host_id and player.get("username") != host_id:
                    await websocket.send_json({"type": "error", "data": "only_host"})
                    continue
                # start the game
                try:
                    gs = game_service.start_game_for_lobby(lobby_id)
                    await manager.broadcast(lobby_id, {"type": "game_started", "data": {"game_id": gs.id}})
                except Exception as e:
                    await websocket.send_json({"type": "error", "data": str(e)})
            else:
                # echo unknown events for now
                await manager.broadcast(lobby_id, {"type": "unknown_event", "data": data})
    except WebSocketDisconnect:
        manager.disconnect(lobby_id, websocket)
        await manager.broadcast(lobby_id, {"type": "lobby_update", "data": {"players": [p.model_dump() for p in _LOBBIES[lobby_id].players]}})