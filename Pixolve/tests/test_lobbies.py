from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_create_and_join_lobby():
    # register and login user
    client.post('/auth/register', json={"username": "host1", "password": "pw"})
    r = client.post('/auth/login', json={"username": "host1", "password": "pw"})
    token = r.json()['access_token']

    # create lobby
    headers = {"Authorization": f"Bearer {token}"}
    r2 = client.post('/lobbies', json={"max_players": 4, "rounds": 1, "host_id": "host1"}, headers=headers)
    assert r2.status_code == 200
    body = r2.json()
    assert 'join_code' in body
    join_code = body['join_code']

    # another player joins by code
    # no auth required to join by code (UI will supply player info)
    join_payload = {"join_code": join_code, "player": {"id": "p2", "username": "p2", "display_name": "P2"}}
    r3 = client.post('/lobbies/join_by_code', json=join_payload)
    assert r3.status_code == 200
    jbody = r3.json()
    assert any(p['username']== 'p2' for p in jbody['players'])
