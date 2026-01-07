import websocket
import json
import requests
import secrets
import sys
import time

BASE_URL = "http://localhost:8000/api/v1"
WS_URL = "ws://localhost:8000/ws"

def test_orb():
    print("Testing Orb System...")
    
    # 1. Setup
    username = f"goku_{secrets.token_hex(4)}"
    password = "password123"
    requests.post(f"{BASE_URL}/auth/signup", json={"username": username, "password": password})
    resp = requests.post(f"{BASE_URL}/auth/login", json={"username": username, "password": password})
    token = resp.json()['access_token']
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.post(f"{BASE_URL}/players/", json={"name": f"Goku_{secrets.token_hex(2)}", "race": "Zenkai"}, headers=headers)
    if resp.status_code != 200:
        print(f"Player Creation Failed: {resp.status_code} {resp.text}")
        sys.exit(1)
    player_id = resp.json()['id']
    
    ws = websocket.create_connection(f"{WS_URL}/{player_id}")
    time.sleep(1)
    
    # Drain welcome
    ws.settimeout(0.5)
    try:
        while True: ws.recv()
    except: pass
    ws.settimeout(5.0)

    # 2. Prevent Premature Invocation
    print("Attempting Wish (Empty)...")
    ws.send("wish")
    msg = json.loads(ws.recv())
    print(f"Log: {msg['content']}")
    if "You do not have all" in msg["content"]:
        print("SUCCESS: Wish rejected.")
    else:
        print("FAILED: Wish check logic broken.")
        
    # 3. Get the Shards
    print("Cheating Shards...")
    ws.send("cheat_shards")
    msg = json.loads(ws.recv()) # "Cheater..."
    print(f"Log: {msg['content']}")
    
    ws.send("inventory")
    msg = json.loads(ws.recv())
    if "Omega Shard" in msg["content"]:
         print("SUCCESS: Shards obtained.")
    
    # 4. Invoke Archon
    print("Summoning Archon...")
    ws.send("wish")
    
    # Provide generous timeout for dramatic messages
    summoned = False
    leveled = False
    
    for _ in range(5):
        try:
            ws.settimeout(2.0)
            msg = json.loads(ws.recv())
            print(f"Log: {msg['content']}")
            if "ARCHON" in msg["content"]:
                summoned = True
            if "gained 5 levels" in msg["content"]:
                leveled = True
            if "dissipate" in msg["content"]:
                break
        except: break

    if summoned and leveled:
        print("SUCCESS: Archon Granted Wish.")
    else:
        print("FAILED: Wish execution incomplete.")

    ws.close()

if __name__ == "__main__":
    test_orb()
