import websocket
import json
import requests
import secrets
import sys
import time

BASE_URL = "http://localhost:8000/api/v1"
WS_URL = "ws://localhost:8000/ws"

def test_inventory():
    print("Testing Inventory System...")
    
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

    # 2. Check Zeni
    print("Checking Inventory (Expect 100 Zeni)...")
    ws.send("inventory")
    msg = json.loads(ws.recv())
    if "Zeni: 100" not in msg["content"]:
        print(f"FAILED: Initial Zeni wrong: {msg['content']}")
    else:
        print("SUCCESS: Initial Zeni correct.")

    # 3. Move to Shop
    # Start -> South -> City Center -> West -> Shop
    print("Moving to Shop...")
    moves = ["south", "west"]
    for m in moves:
        ws.send(m)
        # Drain move + look
        try:
             while True: 
                 m = json.loads(ws.recv())
                 if m.get("type") == "gamestate": break
        except: pass
    
    # 4. Buy Item
    print("Buying Potion...")
    ws.send("buy Healing Capacitor") # Cost 20
    # Log: You bought...
    msg = json.loads(ws.recv())
    print(f"Log: {msg['content']}")
    
    # 5. Verify transaction
    ws.send("inventory")
    msg = json.loads(ws.recv()) # content
    content = msg["content"]
    print(f"Inventory State:\n{content}")
    
    if "Zeni: 80" in content and "Healing Capacitor x1" in content:
        print("SUCCESS: Buying worked.")
    else:
        print("FAILED: Buy transaction failed.")

    # 6. Use Item
    print("Using Potion...")
    ws.send("use Healing Capacitor")
    msg = json.loads(ws.recv())
    print(f"Log: {msg['content']}")
    
    ws.send("inventory")
    msg = json.loads(ws.recv())
    if "Healing Capacitor" not in msg["content"]:
        print("SUCCESS: Item consumed.")
    else:
        print("FAILED: Item not consumed.")

    ws.close()

if __name__ == "__main__":
    test_inventory()
