import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-for-deadit'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///deadit.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Ollama Configuration
    OLLAMA_BASE_URL = os.environ.get('OLLAMA_URL') or 'http://localhost:11434'
    OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL') or 'llama-3.1-8b-local:latest'
    
    # Debug Logging
    DEBUG_AI = os.environ.get('DEBUG_AI', 'True').lower() == 'true'
