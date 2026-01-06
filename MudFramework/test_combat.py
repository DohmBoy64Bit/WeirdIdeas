import websocket
import json
import requests
import secrets
import sys
import time

BASE_URL = "http://localhost:8000/api/v1"
WS_URL = "ws://localhost:8000/ws"

def test_combat_system():
    # 1. Create User/Player
    username = f"fighter_{secrets.token_hex(4)}"
    password = "password123"
    print(f"Creating Fighter {username}...")
    requests.post(f"{BASE_URL}/auth/signup", json={"username": username, "password": password})
    resp = requests.post(f"{BASE_URL}/auth/login", json={"username": username, "password": password})
    token = resp.json()['access_token']
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.post(f"{BASE_URL}/players/", json={"name": f"Goku_{secrets.token_hex(2)}", "race": "Zenkai"}, headers=headers)
    player_id = resp.json()['id']

    # 2. Connect
    ws = websocket.create_connection(f"{WS_URL}/{player_id}")
    # Consume initial messages
    time.sleep(1) 
    while True:
        try:
            ws.settimeout(0.1)
            ws.recv()
        except:
            break
    ws.settimeout(5.0)

    # 3. Hunt (Start Combat)
    print("Sending 'hunt'...")
    ws.send("hunt")
    
    # Expect: "You found a Saibaman!" or similar
    found_combat = False
    for _ in range(5):
        try:
            msg = json.loads(ws.recv())
            if msg.get("channel") == "channel-combat":
                print(f"Combat Log: {msg['content']}")
                found_combat = True
                break
        except: pass
    
    if not found_combat:
        print("FAILED: Did not start combat.")
        sys.exit(1)

    # 4. Attack (Round 1)
    print("Sending 'attack'...")
    ws.send("attack")
    
    # Expect: Damage logs
    logs = []
    for _ in range(5):
        try:
            msg = json.loads(ws.recv())
            if msg.get("channel") == "channel-combat":
                logs.append(msg['content'])
        except: break
    
    if not logs:
        print("FAILED: No combat logs received after attack.")
        sys.exit(1)
        
    for l in logs:
        print(f"   > {l}")
    
    print("SUCCESS: Combat Initialized and Rounds processed!")
    ws.close()

if __name__ == "__main__":
    test_combat_system()
