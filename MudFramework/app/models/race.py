from sqlalchemy import Column, Integer, String, JSON
from app.core.database import Base

class Race(Base):
    __tablename__ = "races"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    description = Column(String)
    base_stats = Column(JSON, default=dict)
    scaling_stats = Column(JSON, default=dict)  # How stats grow per level
    transformations = Column(JSON, default=list)  # List of transformations
    base_flux = Column(Integer, default=100)  # Base Flux energy for this race of transformations
