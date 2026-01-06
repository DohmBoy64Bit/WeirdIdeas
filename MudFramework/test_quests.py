import websocket
import json
import requests
import secrets
import sys
import time
import re

BASE_URL = "http://localhost:8000/api/v1"
WS_URL = "ws://localhost:8000/ws"

def test_quest():
    print("Testing Quest System...")
    
    # 1. Setup
    username = f"trunks_{secrets.token_hex(4)}"
    password = "password123"
    requests.post(f"{BASE_URL}/auth/signup", json={"username": username, "password": password})
    resp = requests.post(f"{BASE_URL}/auth/login", json={"username": username, "password": password})
    if resp.status_code != 200:
        print("Login failed")
        sys.exit(1)
        
    token = resp.json()['access_token']
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.post(f"{BASE_URL}/players/", json={"name": f"Trunks_{secrets.token_hex(2)}", "race": "Terran"}, headers=headers)
    player_id = resp.json()['id']
    
    ws = websocket.create_connection(f"{WS_URL}/{player_id}")
    time.sleep(1) # Wait for connect
    
    # Drain welcome
    ws.settimeout(0.5)
    try:
        while True: ws.recv()
    except: pass
    ws.settimeout(5.0)

    # 2. Move to Capsule Lobby
    print("Moving to Capsule Lobby (North)...")
    ws.send("north")
    # Drain move + look
    try:
         while True: 
             m = json.loads(ws.recv())
             if m.get("type") == "gamestate": break
             if m.get("content") == "You move north...": pass
    except: pass

    # 3. Talk to Bulma
    print("Talking to Bulma...")
    ws.send("talk")
    
    # Consume up to 5 messages looking for confirmation
    started = False
    for _ in range(5):
        try:
            msg = json.loads(ws.recv())
            print(f"Log: {msg['content']}")
            if "Quest Started" in msg['content'] or "Check 'quests'" in msg['content']:
                started = True
                break
        except: break
    
    if started:
        print("SUCCESS: Quest Started.")
    else:
        print("FAILED: Quest not started (or message missed).")

    ws.send("quests")
    for _ in range(3):
        try:
             msg = json.loads(ws.recv())
             print(f"Log: {msg['content']}")
             if "Clean up the Wasteland: 0/3" in msg["content"]:
                 print("SUCCESS: Quest List correct.")
                 break
        except: break

    # 4. Kill 3 Saibamen
    print("Killing 3 Saibamen...")
    for i in range(1, 4):
        print(f"Kill {i}...")
        ws.send("hunt")
        time.sleep(1.0) # Wait for hunt to register
        
        # Kill loop
        dead = False
        attempts = 0
        while not dead and attempts < 20:
             ws.send("attack")
             attempts += 1
             
             # Consume logs derived from attack
             for _ in range(5): # Check more messages
                 try:
                     ws.settimeout(1.0)
                     msg = json.loads(ws.recv())
                     print(f"DEBUG: {msg['content']}") # PRINT EVERYTHING
                     
                     if "Quest Update" in msg.get("content", ""):
                         print(f"Quest Log: {msg['content']}")
                         if f"({i}/3)" in msg['content']:
                             print(f"SUCCESS: Progress {i}/3 confirmed.")
                     
                     if "gained" in msg.get("content", "") and "EXP" in msg.get("content", ""):
                         print(f"Mob {i} defeated.")
                         dead = True
                 except: break
             
             if dead: break
        
        if not dead:
            print(f"WARNING: Failed to kill mob {i} in time.")

    # 5. Complete Quest
    print("Turning in Quest...")
    ws.send("talk")
    
    completed = False
    for _ in range(5):
        try:
            ws.settimeout(1.0)
            msg = json.loads(ws.recv())
            print(f"Log: {msg['content']}")
            if "Quest Completed" in msg["content"]:
                completed = True
        except: break
    
    if completed:
        print("SUCCESS: Quest Completed!")
    else:
        print("FAILED: completion message missing.")

    ws.close()

if __name__ == "__main__":
    test_quest()
