from sqlalchemy import Column, Integer, String, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base

class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    name = Column(String, unique=True, index=True)
    race = Column(String)  # Storing race name directly for now to simplify
    level = Column(Integer, default=1)
    exp = Column(Integer, default=0)
    stats = Column(JSON, default=dict)
    inventory = Column(JSON, default=list)
    current_map = Column(String, default="start_area")
    position = Column(JSON, default=lambda: {"x": 0, "y": 0})
    combat_state = Column(JSON, default=None)  # { "enemy_id": "...", "hp": ... }
    transformation = Column(String, default="Base")
    zeni = Column(Integer, default=100)  # Starting currency
    equipment = Column(JSON, default=dict)  # {"weapon": None, "armor": None}
    learned_skills = Column(JSON, default=list)  # List of skill IDs
    active_quests = Column(JSON, default=dict)  # {"quest_id": {"progress": 0}}
    completed_quests = Column(JSON, default=list)  # ["quest_id"]
    
    user = relationship("User", backref="player")
