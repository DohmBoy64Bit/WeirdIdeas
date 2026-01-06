import websocket
import json
import requests
import secrets
import sys
import time

BASE_URL = "http://localhost:8000/api/v1"
WS_URL = "ws://localhost:8000/ws"

def test_boss_spawn():
    print("Testing Boss Spawn (Frieza)...")
    
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
        while True: ws.recv()
    except: pass

    # Route: Start -> North (Capsule) -> South (Start) -> East (City) -> East (Wasteland 1) -> East (Wasteland 2) -> North (Landing) -> Enter (Interior)
    # Wait, Map:
    # Start -> N (Capsule) || E (City)
    # City -> E (Wasteland 1)
    # Wasteland 1 -> E (Wasteland 2)
    # Wasteland 2 -> N (Landing)
    # Landing -> Enter (Interior)
    
    path = ["east", "east", "east", "north", "enter"]
    
    print("Navigating to Frieza's Ship...")
    for move in path:
        print(f"> Sending {move}")
        ws.send(move)
        time.sleep(0.2)
        # Drain messages
        try:
            while True: 
                msg = json.loads(ws.recv())
                if msg.get("type") == "gamestate" and "room" in msg:
                    print(f"  Reached: {msg['room']['name']}")
        except: pass
        
    # Check if we are in Interior
    # (The loop above drains socket, so we might need to check explicitly by 'look' or trusting the flow)
    # I'll `look` to confirm.
    ws.send("look")
    time.sleep(0.5)
    in_ship = False
    try:
         msg = json.loads(ws.recv())
         # This might be gamestate or chat.
         # Actually gamestate comes on connect or look?
         # look -> sends gamestate.
         if msg.get("type") == "gamestate":
             if "Frieza's Ship" in msg["room"]["name"]:
                 in_ship = True
    except: pass
    
    if in_ship:
        print("SUCCESS: Inside Ship.")
    else:
        # Retry read loop
        try:
             while True:
                msg = json.loads(ws.recv())
                if msg.get("type") == "gamestate" and "Frieza's Ship" in msg["room"]["name"]:
                     in_ship = True
                     print("SUCCESS: Inside Ship (Delayed).")
                     break
        except: pass

    # Hunt Boss
    print("Hunting for Frieza...")
    ws.send("hunt")
    
    found_frieza = False
    for _ in range(10):
        try:
             msg = json.loads(ws.recv())
             if "Lord Frieza" in msg.get("content", ""):
                 found_frieza = True
                 print(f"SUCCESS: Found Boss - {msg['content']}")
                 break
        except: break

    if not found_frieza:
        print("FAILED: Could not find Frieza.")
        sys.exit(1)

    # Optional: Suicide Attack
    print("Suicide Attack...")
    ws.send("attack")
    time.sleep(1)
    # Just close, we know he's there.

    ws.close()

if __name__ == "__main__":
    test_boss_spawn()
