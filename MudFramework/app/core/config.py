from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "DBZ MUD Framework"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = "sqlite:///./mud.db"
    
    class Config:
        env_file = ".env"

settings = Settings()
