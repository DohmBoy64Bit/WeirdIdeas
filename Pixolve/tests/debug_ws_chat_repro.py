import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def repro():
    client.post('/auth/register', json={"username": "chat_host", "password": "pw"})
    r = client.post('/auth/login', json={"username": "chat_host", "password": "pw"})
    host_token = r.json()['access_token']

    client.post('/auth/register', json={"username": "chat_p1", "password": "pw"})
    r2 = client.post('/auth/login', json={"username": "chat_p1", "password": "pw"})
    p1_token = r2.json()['access_token']

    headers = {"Authorization": f"Bearer {host_token}"}
    r3 = client.post('/lobbies', json={"max_players": 4, "rounds": 1, "host_id": "chat_host"}, headers=headers)
    lobby = r3.json()

    join_payload = {"join_code": lobby['join_code'], "player": {"id": "chat_p1", "username": "chat_p1", "display_name": "P1"}}
    client.post('/lobbies/join_by_code', json=join_payload)

    with client.websocket_connect(f"/ws?token={host_token}&lobby={lobby['id']}") as ws_host:
        with client.websocket_connect(f"/ws?token={p1_token}&lobby={lobby['id']}") as ws_p1:
            print('connected')
            print('ws_host methods:', [m for m in dir(ws_host) if not m.startswith('_')])
            print('ws_p1 methods:', [m for m in dir(ws_p1) if not m.startswith('_')])
            try:
                print('host initial (blocking receive attempt):', ws_host.receive_json())
            except Exception as e:
                print('host initial none or blocked', e)
            try:
                print('p1 initial (blocking receive attempt):', ws_p1.receive_json())
            except Exception as e:
                print('p1 initial none or blocked', e)

            print('host sending chat')
            ws_host.send_json({"type": "chat", "data": {"player": "chat_host", "text": "hello!"}})

            # Try raw receive() calls with short timeouts to detect incoming frames
            for name, ws in [('host', ws_host), ('p1', ws_p1)]:
                try:
                    print(f"{name} receive raw (timeout=1):", ws.receive(timeout=1))
                except Exception as e:
                    print(f"{name} receive raw error:", e)
            # Also try receive_json (blocking) once each
            try:
                print('host receive_json blocking:', ws_host.receive_json())
            except Exception as e:
                print('host receive_json error:', e)
            try:
                print('p1 receive_json blocking:', ws_p1.receive_json())
            except Exception as e:
                print('p1 receive_json error:', e)


if __name__ == '__main__':
    repro()
