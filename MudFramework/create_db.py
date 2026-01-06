from app.core.database import Base, engine
# Import models to ensure they are registered with Base metadata
from app.models.base import User, Player, Race

def init_db():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created.")

if __name__ == "__main__":
    init_db()
