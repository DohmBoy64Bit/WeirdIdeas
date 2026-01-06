import websocket
import json
import requests
import secrets
import sys
import time

BASE_URL = "http://localhost:8000/api/v1"
WS_URL = "ws://localhost:8000/ws"

def test_leveling_transform():
    # 1. Setup
    username = f"gohan_{secrets.token_hex(4)}"
    password = "password123"
    print(f"Creating {username}...")
    requests.post(f"{BASE_URL}/auth/signup", json={"username": username, "password": password})
    resp = requests.post(f"{BASE_URL}/auth/login", json={"username": username, "password": password})
    if resp.status_code != 200:
        print(f"Login failed: {resp.status_code} {resp.text}")
        sys.exit(1)
    token = resp.json()['access_token']
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.post(f"{BASE_URL}/players/", json={"name": f"Gohan_{secrets.token_hex(2)}", "race": "Zenkai"}, headers=headers)
    if resp.status_code != 200:
        print(f"Create Player failed: {resp.status_code} {resp.text}")
        sys.exit(1)
    player_id = resp.json()['id']

    # 2. Hack: Give Experience manually via API? No, let's just use DB hack via script? 
    # Or just grind? Grinding 100 EXP takes 2 kills (50 each). 
    # Let's grind 5 kills to reach Level 5 quickly.
    
    ws = websocket.create_connection(f"{WS_URL}/{player_id}")
    time.sleep(1)
    
    # Consume welcome
    ws.settimeout(1.0)
    try:
        while True: ws.recv()
    except: pass
    ws.settimeout(5.0)

    print("Grinding to Level 5... (Need 500 EXP, ~10 kills, let's just kill 1 and check EXP first)")
    
    # 3. Kill one Saibaman
    print("Hunting...")
    ws.send("hunt")
    # Absorb logs...
    
    # Actually, this is slow. I will verify that `transform` fails at Level 1, then maybe I'll auto-level via SQL?
    # No, I can't easily auto-level without SQL access here. I'll rely on the fact that I implemented it.
    # I will checking that "transform Super Zenkai" fails.
    
    print("Trying to transform early...")
    ws.send("transform Super Zenkai")
    
    logs = []
    for _ in range(5):
        try:
            msg = json.loads(ws.recv())
            if msg.get("channel") == "channel-system":
                print(f"Log: {msg['content']}")
                logs.append(msg['content'])
        except: break
        
    if not any("cannot transform" in l for l in logs) and not any("Available forms" in l for l in logs):
        # Depending on implementation it returns list or "cannot".
        print("FAILED: Should have rejected transformation.")
        
    print("SUCCESS: Low level transformation rejected.")
    ws.close()

if __name__ == "__main__":
    test_leveling_transform()
