from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.race import Race
from app.schemas.race import RaceResponse

router = APIRouter()

@router.get("/", response_model=List[RaceResponse])
def get_races(db: Session = Depends(get_db)):
    races = db.query(Race).all()
    return races
