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
    
    # Automation Settings
    # Seconds between "Deadit Life Cycle" checks (default: 5 minutes)
    # Seconds between "Deadit Life Cycle" checks (default: 5 minutes)
    RUMBLE_INTERVAL = int(os.environ.get('RUMBLE_INTERVAL', 300))
    # Chance to create a NEW thread (0.0 to 1.0)
    RUMBLE_NEW_THREAD_CHANCE = float(os.environ.get('RUMBLE_NEW_THREAD_CHANCE', 0.10))
    # Chance to REPLY to an existing thread (0.0 to 1.0)
    RUMBLE_REPLY_CHANCE = float(os.environ.get('RUMBLE_REPLY_CHANCE', 0.40))
    SCHEDULER_API_ENABLED = True
