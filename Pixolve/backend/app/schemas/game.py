from pydantic import BaseModel
from typing import List, Optional

class RevealStep(BaseModel):
    step_index: int
    pixelation: int  # e.g., 32, 16, 8, 4, 0
    time_offset: float  # seconds from round start

class RoundState(BaseModel):
    round_index: int
    image_id: str
    reveal_steps: List[RevealStep]
    duration_secs: int
    correct_answer: Optional[str] = None  # normalized answer string for testing/verification

class GuessIn(BaseModel):
    player_id: str
    text: str

class GuessResult(BaseModel):
    player_id: str
    correct: bool
    points_awarded: int = 0

class GameState(BaseModel):
    id: str
    lobby_id: str
    round_index: int
    rounds: List[RoundState]
    players: List[str]
    finished: bool = False