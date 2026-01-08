from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api import deps
from app.models.user import User
from app.models.player import Player
from app.models.race import Race
from app.schemas.player import PlayerCreate, PlayerResponse
from app.core.constants import BASE_FLUX, FLUX_PER_INT

router = APIRouter()

@router.post("/", response_model=PlayerResponse)
def create_player(player_in: PlayerCreate, current_user: User = Depends(deps.get_current_user), db: Session = Depends(get_db)):
    if db.query(Player).filter(Player.user_id == current_user.id).first():
        raise HTTPException(status_code=400, detail="User already has a player character.")
    
    if db.query(Player).filter(Player.name == player_in.name).first():
        raise HTTPException(status_code=400, detail="Character name already taken.")

    # Get Race Stats
    race = db.query(Race).filter(Race.name == player_in.race).first()
    if not race:
         raise HTTPException(status_code=404, detail="Race not found.")

    # Initialize stats
    stats = race.base_stats.copy()
    stats["hp"] = stats["vit"] * 10
    stats["max_hp"] = stats["vit"] * 10
    
    # Initialize Flux: base_flux + (INT * FLUX_PER_INT)
    base_flux = race.base_flux if race.base_flux else BASE_FLUX
    max_flux = base_flux + (stats.get("int", 0) * FLUX_PER_INT)
    stats["flux"] = max_flux
    stats["max_flux"] = max_flux
    
    player = Player(
        user_id=current_user.id,
        name=player_in.name,
        race=player_in.race,
        stats=stats, # Use the calculated stats
        current_map="start_area",
        position={"x": 0, "y": 0}
    )
    db.add(player)
    db.commit()
    db.refresh(player)
    return player

@router.get("/me", response_model=PlayerResponse)
def get_my_player(current_user: User = Depends(deps.get_current_user), db: Session = Depends(get_db)):
    player = db.query(Player).filter(Player.user_id == current_user.id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found for this user.")
    return player
