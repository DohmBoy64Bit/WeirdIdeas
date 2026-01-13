"""Game service: manage game lifecycle and broadcast reveal steps via WebSocket manager.
This is a simple, in-memory implementation suitable for MVP and testing.
"""
import asyncio
import uuid
from typing import Dict, List
from datetime import datetime, timezone

from ..schemas.game import RoundState, RevealStep, GameState
from ..sockets.ws_manager import manager
from ..api.lobbies import _LOBBIES

GAMES: Dict[str, GameState] = {}

DEFAULT_PIXEL_STEPS = [32, 16, 8, 4, 0]
DEFAULT_ROUND_DURATION = 20  # seconds

# Per-game runtime state: scores and current round start times
# structure: RUNTIME[game_id] = {"scores": {player_id: points}, "round_started_at": datetime}
RUNTIME: Dict[str, dict] = {}

async def _run_round_and_broadcast(game_id: str, lobby_id: str, round_state: RoundState):
    # Broadcast start_round
    await manager.broadcast(lobby_id, {"type": "start_round", "data": {"round_index": round_state.round_index, "image_id": round_state.image_id}})

    # record round start time
    from datetime import datetime, timezone
    RUNTIME.setdefault(game_id, {})["round_started_at"] = datetime.now(timezone.utc)
    RUNTIME.setdefault(game_id, {})["current_round_index"] = round_state.round_index

    # Initialize scores map if not present
    RUNTIME.setdefault(game_id, {}).setdefault("scores", {})
    RUNTIME.setdefault(game_id, {}).setdefault("correct_this_round", set())

    # Compute intervals between steps
    steps = round_state.reveal_steps
    # Each step's time_offset is relative to round start; schedule according to those offsets
    last_offset = 0.0
    for step in steps:
        interval = step.time_offset - last_offset
        if interval > 0:
            await asyncio.sleep(interval)
        # broadcast reveal_step
        await manager.broadcast(lobby_id, {"type": "reveal_step", "data": step.model_dump()})
        last_offset = step.time_offset

    # End of round
    # Clear correct_this_round set
    RUNTIME[game_id]["correct_this_round"].clear()
    await manager.broadcast(lobby_id, {"type": "end_round", "data": {"round_index": round_state.round_index}})


def _make_reveal_steps(duration_secs: int) -> List[RevealStep]:
    # Spread DEFAULT_PIXEL_STEPS evenly across duration
    count = len(DEFAULT_PIXEL_STEPS)
    steps: List[RevealStep] = []
    for i, px in enumerate(DEFAULT_PIXEL_STEPS):
        time_offset = round((i / (count - 1)) * duration_secs, 2) if count > 1 else 0
        steps.append(RevealStep(step_index=i, pixelation=px, time_offset=time_offset))
    return steps


def process_guess_for_lobby(lobby_id: str, player_id: str, text: str) -> dict:
    """Process a guess: check correctness against current running game for the lobby, award points if correct and not previously guessed in the round.
    Returns a result dict suitable for broadcasting: {player_id, correct, points_awarded, round_index}
    """
    # find game for this lobby
    for g in GAMES.values():
        if g.lobby_id == lobby_id:
            game = g
            break
    else:
        raise ValueError("no_active_game")

    gid = game.id
    runtime = RUNTIME.get(gid)
    if not runtime:
        raise ValueError("runtime_missing")
    current_round_idx = runtime.get("current_round_index")
    if current_round_idx is None:
        raise ValueError("no_round_in_progress")

    round_state = game.rounds[current_round_idx]
    if player_id in runtime.get("correct_this_round", set()):
        return {"player_id": player_id, "correct": False, "points_awarded": 0, "round_index": current_round_idx, "reason": "already_correct"}

    # normalize guess and answer (simple lowercase trim)
    norm_guess = (text or "").strip().lower()
    norm_answer = (round_state.correct_answer or "").strip().lower()
    if norm_guess == norm_answer:
        # compute time elapsed
        from datetime import datetime, timezone
        started = runtime.get("round_started_at")
        if not started:
            return {"player_id": player_id, "correct": False, "points_awarded": 0, "round_index": current_round_idx, "reason": "timing_missing"}
        elapsed = (datetime.now(timezone.utc) - started).total_seconds()
        from .scoring import compute_points
        points = compute_points(elapsed, round_state.duration_secs)
        # award points
        runtime.setdefault("scores", {}).setdefault(player_id, 0)
        runtime["scores"][player_id] += points
        runtime.setdefault("correct_this_round", set()).add(player_id)
        # award XP to user (XP = points // 10)
        from ..services import auth_service
        xp = points // 10
        try:
            auth_service.add_xp(player_id, xp)
        except Exception:
            # best-effort: ignore if user not found (guest players)
            pass
        return {"player_id": player_id, "correct": True, "points_awarded": points, "xp_awarded": xp, "round_index": current_round_idx}

    # incorrect guess (simple flow)
    return {"player_id": player_id, "correct": False, "points_awarded": 0, "round_index": current_round_idx}


# Public API: start game for a lobby
def start_game_for_lobby(lobby_id: str) -> GameState:
    """Create and start a game for the given lobby. Returns the GameState."""
    lobby = _LOBBIES.get(lobby_id)
    if not lobby:
        raise ValueError("lobby_not_found")

    # Get category and images
    from ..services import category_service
    import os
    import random
    
    category_id = lobby.category
    category = category_service.get_category(category_id) if category_id else None
    image_paths = []
    
    if category and category.get('images'):
        image_paths = category['images']
    else:
        # Fallback: use placeholder
        image_paths = ['placeholder.png']
    
    # Select random images for rounds (with replacement if needed)
    selected_images = []
    for r in range(lobby.rounds):
        if image_paths:
            selected_images.append(random.choice(image_paths))
        else:
            selected_images.append('placeholder.png')
    
    # Helper to extract answer from image filename
    def get_answer_from_image_path(img_path: str) -> str:
        """Extract answer from image path (filename without extension)."""
        filename = os.path.basename(img_path)
        # Remove extension
        name = os.path.splitext(filename)[0]
        # Remove UUID prefix if present (format: uuid_filename.ext)
        if '_' in name:
            parts = name.split('_', 1)
            if len(parts) > 1 and len(parts[0]) == 36:  # UUID length
                name = parts[1]
        return name.strip()

    game_id = str(uuid.uuid4())
    rounds: List[RoundState] = []
    for r in range(lobby.rounds):
        img_path = selected_images[r]
        answer = get_answer_from_image_path(img_path)
        # Store relative path for serving
        image_url = f"/data/{img_path}" if img_path != 'placeholder.png' else "/placeholder.png"
        rs = RoundState(
            round_index=r,
            image_id=image_url,
            reveal_steps=_make_reveal_steps(DEFAULT_ROUND_DURATION),
            duration_secs=DEFAULT_ROUND_DURATION,
            correct_answer=answer
        )
        rounds.append(rs)

    gs = GameState(id=game_id, lobby_id=lobby_id, round_index=0, rounds=rounds, players=[p.id for p in lobby.players], finished=False)
    GAMES[game_id] = gs

    # initialize runtime
    RUNTIME[game_id] = {"scores": {}, "round_started_at": None, "current_round_index": None, "correct_this_round": set()}

    async def run_game():
        for rs in rounds:
            await _run_round_and_broadcast(game_id, lobby_id, rs)
        # mark finished
        gs.finished = True
        # Get final scores from runtime
        runtime = RUNTIME.get(game_id, {})
        final_scores = runtime.get("scores", {})
        await manager.broadcast(lobby_id, {
            "type": "game_finished", 
            "data": {
                "game_id": game_id,
                "scores": final_scores
            }
        })

    # Schedule the run_game coroutine — if there's an active loop, create a task, otherwise run in a background thread
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(run_game())
    except RuntimeError:
        # No running loop (typical in unit tests), run the coroutine in a new event loop in a daemon thread
        import threading
        t = threading.Thread(target=lambda: asyncio.run(run_game()), daemon=True)
        t.start()

    return gs