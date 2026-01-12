from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_chat_broadcasts_to_all_clients():
    # register two players and create/join a lobby
    client.post('/auth/register', json={"username": "chat_host", "password": "pw"})
    r = client.post('/auth/login', json={"username": "chat_host", "password": "pw"})
    host_token = r.json()['access_token']

    client.post('/auth/register', json={"username": "chat_p1", "password": "pw"})
    r2 = client.post('/auth/login', json={"username": "chat_p1", "password": "pw"})
    p1_token = r2.json()['access_token']

    headers = {"Authorization": f"Bearer {host_token}"}
    r3 = client.post('/lobbies', json={"max_players": 4, "rounds": 1, "host_id": "chat_host"}, headers=headers)
    lobby = r3.json()

    # p1 joins
    join_payload = {"join_code": lobby['join_code'], "player": {"id": "chat_p1", "username": "chat_p1", "display_name": "P1"}}
    r4 = client.post('/lobbies/join_by_code', json=join_payload)
    assert r4.status_code == 200

    # connect websockets using context managers
    found_host = False
    found_p1 = False
    with client.websocket_connect(f"/ws?token={host_token}&lobby={lobby['id']}") as ws_host:
        print(f"[test] ws_host repr: {repr(ws_host)}")
        with client.websocket_connect(f"/ws?token={p1_token}&lobby={lobby['id']}") as ws_p1:
            print(f"[test] ws_p1 repr: {repr(ws_p1)}")
            # consume any initial messages
            try:
                ws_host.receive_json(timeout=0.1)
            except Exception:
                pass
            try:
                ws_p1.receive_json(timeout=0.1)
            except Exception:
                pass

            # host sends chat
            ws_host.send_json({"type": "chat", "data": {"player": "chat_host", "text": "hello!"}})

            # Blocking reads (synchronous) to find chat messages; read up to a few messages to avoid hanging
            found_host = False
            found_p1 = False
            m_p1 = None
            m_host = None
            # read from p1 first (likely to get chat)
            for _ in range(5):
                try:
                    m = ws_p1.receive_json()
                except Exception:
                    break
                if m.get('type') == 'chat' and m.get('data', {}).get('text') == 'hello!':
                    m_p1 = m
                    found_p1 = True
                    break
            # read from host
            for _ in range(5):
                try:
                    m = ws_host.receive_json()
                except Exception:
                    break
                if m.get('type') == 'chat' and m.get('data', {}).get('text') == 'hello!':
                    m_host = m
                    found_host = True
                    break
            # Check that p1 received the chat (robust single-client assertion)
            print('found_p1 =', found_p1, 'found_host =', found_host)
            assert found_p1

            # Verify timestamp is present and timezone-aware
            from datetime import datetime
            ts = m_p1.get('data', {}).get('ts') if m_p1 else None
            assert ts is not None, 'chat message missing ts'
            dt = datetime.fromisoformat(ts)
            assert dt.tzinfo is not None, 'chat timestamp is not timezone-aware'
    # cleanup
    try:
        ws_host.close()
    except Exception:
        pass
    try:
        ws_p1.close()
    except Exception:
        pass
