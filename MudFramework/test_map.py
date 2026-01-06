import websocket
import json
import requests
import secrets
import sys
import time

BASE_URL = "http://localhost:8000/api/v1"
WS_URL = "ws://localhost:8000/ws"

def test_map_system():
    # 1. Create User & Player
    username = f"walker_{secrets.token_hex(4)}"
    password = "password123"
    print(f"1. Creating user {username}...")
    
    # Signup
    requests.post(f"{BASE_URL}/auth/signup", json={"username": username, "password": password})
    # Login
    resp = requests.post(f"{BASE_URL}/auth/login", json={"username": username, "password": password})
    token = resp.json()['access_token']
    headers = {"Authorization": f"Bearer {token}"}
    # Create Char
    resp = requests.post(f"{BASE_URL}/players/", json={"name": f"Walker_{secrets.token_hex(2)}", "race": "Terran"}, headers=headers)
    player_id = resp.json()['id']
    print(f"   Player ID: {player_id}")

    # 2. Connect WebSocket
    print("2. Connecting via WebSocket...")
    ws = websocket.create_connection(f"{WS_URL}/{player_id}")
    
    # 3. Wait for Initial Look
    # We expect a "gamestate" message with room info immediately
    print("3. Waiting for initial Room state...")
    found_room = False
    for _ in range(5):
        msg = json.loads(ws.recv())
        if msg.get("type") == "gamestate" and "room" in msg:
            print(f"   Room: {msg['room']['name']}")
            print(f"   Desc: {msg['room']['description']}")
            found_room = True
            break
    
    if not found_room:
        print("FAILED: Did not receive initial room state.")
        sys.exit(1)

    # 4. Move North
    print("4. Sending 'north' command...")
    ws.send("north")
    
    # 5. Check response
    # Expect: System msg "You move north..." -> Gamestate (New Room)
    found_move = False
    for _ in range(5):
        msg = json.loads(ws.recv())
        if msg.get("type") == "gamestate" and "room" in msg:
            print(f"   New Room: {msg['room']['name']}")
            if msg['room']['name'] == "Capsule Corp Lobby":
                found_move = True
                break
    
    if found_move:
        print("SUCCESS: Map Movement verified!")
    else:
        print("FAILED: Did not move to new room.")
        sys.exit(1)

    ws.close()

if __name__ == "__main__":
    test_map_system()
