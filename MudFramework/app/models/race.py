from sqlalchemy import Column, Integer, String, JSON
from app.core.database import Base

class Race(Base):
    __tablename__ = "races"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    description = Column(String)
    base_stats = Column(JSON)
    scaling_stats = Column(JSON) # How stats grow per level
    transformations = Column(JSON) # List of transformations
