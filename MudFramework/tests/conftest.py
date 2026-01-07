"""
Pytest configuration and shared fixtures
"""
import pytest
import requests
import websocket
import secrets
import time
import json

BASE_URL = "http://localhost:8000/api/v1"
WS_URL = "ws://localhost:8000/ws"

@pytest.fixture
def test_credentials():
    """Generate unique test credentials for each test"""
    username = f"test_{secrets.token_hex(6)}"  # Longer hex for more uniqueness
    password = "TestPass123!"
    return {"username": username, "password": password}

@pytest.fixture
def auth_token(test_credentials):
    """Create account and get auth token"""
    # Signup
    resp = requests.post(f"{BASE_URL}/auth/signup", json=test_credentials)
    if resp.status_code != 200:
        raise Exception(f"Signup failed: {resp.json()}")
    
    # Login
    resp = requests.post(f"{BASE_URL}/auth/login", json=test_credentials)
    if resp.status_code != 200:
        raise Exception(f"Login failed: {resp.json()}")
    
    return resp.json()['access_token']

@pytest.fixture
def auth_headers(auth_token):
    """Generate authorization headers"""
    return {"Authorization": f"Bearer {auth_token}"}

@pytest.fixture
def test_player(auth_headers):
    """Create a test character"""
    char_data = {
        "name": f"TestHero_{secrets.token_hex(4)}",
        "race": "Zenkai"
    }
    resp = requests.post(f"{BASE_URL}/players/", json=char_data, headers=auth_headers)
    if resp.status_code != 200:
        raise Exception(f"Failed to create character: {resp.json()}")
    
    player = resp.json()
    return player

@pytest.fixture
def ws_connection(test_player):
    """Create WebSocket connection"""
    ws = websocket.create_connection(f"{WS_URL}/{test_player['id']}")
    time.sleep(0.5)
    
    # Clear initial messages
    ws.settimeout(0.1)
    try:
        while True:
            ws.recv()
    except:
        pass
    
    ws.settimeout(5.0)
    
    yield ws
    
    # Cleanup
    try:
        ws.close()
    except:
        pass

def send_command(ws, command):
    """Send a command and collect responses"""
    ws.send(command)
    time.sleep(0.5)
    
    messages = []
    ws.settimeout(0.1)
    try:
        while True:
            msg = json.loads(ws.recv())
            messages.append(msg)
    except:
        pass
    
    ws.settimeout(5.0)
    return messages
