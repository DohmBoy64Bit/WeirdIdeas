from sqlalchemy import Column, Integer, String, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base

class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    name = Column(String, unique=True, index=True)
    race = Column(String) # Storing race name directly for now to simplify
    level = Column(Integer, default=1)
    exp = Column(Integer, default=0)
    stats = Column(JSON, default={}) 
    inventory = Column(JSON, default=[])
    current_map = Column(String, default="start_area")
    position = Column(JSON, default={"x": 0, "y": 0})
    
    user = relationship("User", backref="player")
