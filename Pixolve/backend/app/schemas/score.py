from pydantic import BaseModel

class Score(BaseModel):
    player_id: str
    points: int
    correct_guesses: int = 0
    rank: int = 0