# backend/app/main.py
from fastapi import FastAPI
from .core import create_app
import asyncio
import threading
from datetime import timedelta

app = create_app()

# Background task to clean up expired tokens periodically
def cleanup_tokens_periodically():
    """Run token cleanup every hour."""
    import time
    from .services import auth_service
    
    while True:
        try:
            time.sleep(3600)  # Sleep for 1 hour
            removed = auth_service.prune_expired_tokens()
            if removed > 0:
                print(f"Cleaned up {removed} expired tokens")
        except Exception as e:
            print(f"Error in token cleanup: {e}")

# Start background cleanup thread
cleanup_thread = threading.Thread(target=cleanup_tokens_periodically, daemon=True)
cleanup_thread.start()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)