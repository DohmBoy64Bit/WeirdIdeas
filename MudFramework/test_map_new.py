import websocket
import json
import requests
import secrets
import sys
import time

BASE_URL = "http://localhost:8000/api/v1"
WS_URL = "ws://localhost:8000/ws"

def test_map_expansion():
    print("Testing Map Expansion...")
    
    # 1. Setup
    username = f"explorer_{secrets.token_hex(4)}"
    password = "password123"
    requests.post(f"{BASE_URL}/auth/signup", json={"username": username, "password": password})
    resp = requests.post(f"{BASE_URL}/auth/login", json={"username": username, "password": password})
    token = resp.json()['access_token']
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.post(f"{BASE_URL}/players/", json={"name": f"Dora_{secrets.token_hex(2)}", "race": "Terran"}, headers=headers)
    player_id = resp.json()['id']
    
    ws = websocket.create_connection(f"{WS_URL}/{player_id}")
    time.sleep(1)
    ws.settimeout(2.0)
    try:
        while True: ws.recv()
    except: pass

    # 2. Start Area (No Mobs)
    print("In Start Area. Trying to hunt...")
    ws.send("hunt")
    msg = json.loads(ws.recv())
    print(f"Log: {msg['content']}")
    if "nothing to hunt" in msg["content"]:
        print("SUCCESS: Safe Zone confirmed.")
    else:
        print("FAILED: Hunted in safe zone?")

    # 3. Move to Wasteland (East -> East)
    print("Moving East to City Center...")
    ws.send("east")
    time.sleep(0.5)
    
    print("Moving East to Wasteland...")
    ws.send("east")
    time.sleep(0.5)
    
    # 4. Hunt in Wasteland
    print("Hunting in Wasteland...")
    ws.send("hunt")
    
    try:
        msg = json.loads(ws.recv())
        print(f"Log: {msg['content']}") # Look/Move or Hunt?
        # Might get move msg first if not consumed?
        # I consumed loops via sleep/timeout? No.
        # Let's read until we see hunt result.
        
        found = False
        for _ in range(10):
             msg = json.loads(ws.recv())
             if msg.get("type") == "gamestate":
                 continue
                 
             if "content" in msg:
                 print(f"Log: {msg['content']}")
                 if "Combat started" in msg["content"]:
                     found = True
                     print(f"SUCCESS: Found {msg['content']}")
                     break
        
        if not found:
             print("FAILED: No combat in Wasteland.")
             
    except Exception as e:
        print(f"Error: {e}")

    ws.close()

if __name__ == "__main__":
    test_map_expansion()
