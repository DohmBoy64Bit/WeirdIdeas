import websocket
import json
import requests
import secrets
import sys
import time

BASE_URL = "http://localhost:8000/api/v1"
WS_URL = "ws://localhost:8000/ws"

def test_boss_spawn():
    print("Testing Boss Spawn (Xenon Warlord)...")
    
    # 1. Setup
    username = f"trunks_{secrets.token_hex(4)}"
    password = "password123"
    requests.post(f"{BASE_URL}/auth/signup", json={"username": username, "password": password})
    resp = requests.post(f"{BASE_URL}/auth/login", json={"username": username, "password": password})
    token = resp.json()['access_token']
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.post(f"{BASE_URL}/players/", json={"name": f"Trunks_{secrets.token_hex(2)}", "race": "Vitalis"}, headers=headers)
    player_id = resp.json()['id']
    
    ws = websocket.create_connection(f"{WS_URL}/{player_id}")
    time.sleep(1)
    ws.settimeout(2.0)
    try:
        while True: ws.recv() # Drain welcome messages
    except: pass

    # 2. Navigate to Ship and Hunt
    # Path: Start -> East -> Neon City -> East -> Wasteland 1 -> East -> Wasteland 2 -> North -> Landing -> Enter -> Ship
    path = ["east", "east", "east", "north", "enter"]
    
    print("Navigating to Vanguard Ship...")
    for move in path:
        ws.send(move)
        try:
            res = ws.recv()
            # print(res)
        except: pass
        time.sleep(1.0)

    ws.send("look")
    try:
        msg = json.loads(ws.recv())
        if "Vanguard Command Ship" in msg["room"]["name"]:
            print("SUCCESS: Reached Boss Room.")
        else:
            print(f"FAILED: In {msg['room']['name']}")
    except Exception as e:
        print(f"FAILED: Error checking room: {e}")

    # 3. Hunt Boss
    print("Hunting Boss...")
    ws.send("hunt")
    
    found_boss = False
    for _ in range(5):
        try:
             res = ws.recv()
             data = json.loads(res)
             if data["type"] == "chat" and "Xenon Warlord" in data["content"]:
                 print("SUCCESS: Found Boss (Xenon Warlord).")
                 found_boss = True
                 break
        except: pass
    
    if not found_boss:
        print("FAILED: Boss not found.")
        sys.exit(1)

    print("Suicide Attack...")
    ws.send("attack")
    time.sleep(1)
    ws.close()

if __name__ == "__main__":
    test_boss_spawn()
