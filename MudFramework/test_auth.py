import requests
import secrets
import sys

BASE_URL = "http://localhost:8000/api/v1/auth"

def test_auth():
    username = f"user_{secrets.token_hex(4)}"
    password = "password123"
    
    # 1. Signup
    print(f"Signing up {username}...")
    try:
        resp = requests.post(f"{BASE_URL}/signup", json={"username": username, "password": password})
        if resp.status_code != 200:
            print(f"Signup failed: {resp.text}")
            sys.exit(1)
        data = resp.json()
        recovery_code = data['recovery_code']
        print(f"Signup success! Recovery Code: {recovery_code}")
        
        # 2. Login
        print("Logging in...")
        resp = requests.post(f"{BASE_URL}/login", json={"username": username, "password": password})
        if resp.status_code != 200:
            print(f"Login failed: {resp.text}")
            sys.exit(1)
        token = resp.json()['access_token']
        print(f"Login success! Token: {token[:10]}...")
        
        # 3. Recover
        print("Testing Recovery...")
        new_password = "newpassword456"
        resp = requests.post(f"{BASE_URL}/recover", json={"username": username, "recovery_code": recovery_code, "new_password": new_password})
        if resp.status_code != 200:
            print(f"Recovery failed: {resp.text}")
            sys.exit(1)
        token = resp.json()['access_token']
        print(f"Recovery success! New Token: {token[:10]}...")
        
        # 4. Login with new password
        print("Logging in with new password...")
        resp = requests.post(f"{BASE_URL}/login", json={"username": username, "password": new_password})
        if resp.status_code != 200:
            print(f"Login with new password failed: {resp.text}")
            sys.exit(1)
        print("Login with new password success!")
        print("ALL TESTS PASSED")
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_auth()
