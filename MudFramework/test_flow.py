import requests
import secrets
import sys

BASE_URL = "http://localhost:8000/api/v1"

def test_frontend_flow():
    username = f"player_{secrets.token_hex(4)}"
    password = "password123"
    
    # 1. Signup
    print(f"1. Signing up {username}...")
    resp = requests.post(f"{BASE_URL}/auth/signup", json={"username": username, "password": password})
    if resp.status_code != 200:
        print(f"Signup failed: {resp.text}")
        sys.exit(1)
    
    # 2. Login
    print("2. Logging in...")
    resp = requests.post(f"{BASE_URL}/auth/login", json={"username": username, "password": password})
    token = resp.json()['access_token']
    headers = {"Authorization": f"Bearer {token}"}
    
    # 3. Check Routes (Simulate Frontend Checks)
    print("3. Checking Player Status (Expected 404)...")
    resp = requests.get(f"{BASE_URL}/players/me", headers=headers)
    if resp.status_code != 404:
        print(f"Expected 404, got {resp.status_code}")
        sys.exit(1)

    # 4. Create Character
    print("4. Creating Character...")
    char_name = f"Hero_{secrets.token_hex(2)}"
    resp = requests.post(f"{BASE_URL}/players/", json={"name": char_name, "race": "Zenkai"}, headers=headers)
    if resp.status_code != 200:
        print(f"Create Character failed: {resp.text}")
        sys.exit(1)
    player_data = resp.json()
    print(f"Character Created: {player_data['name']} (Race: {player_data['race']})")

    # 5. Check Player Status Again
    print("5. Checking Player Status (Expected 200)...")
    resp = requests.get(f"{BASE_URL}/players/me", headers=headers)
    if resp.status_code != 200:
        print(f"Expected 200, got {resp.status_code}")
        sys.exit(1)
    
    print("Frontend API Flow Verified Successfully!")

if __name__ == "__main__":
    test_frontend_flow()
