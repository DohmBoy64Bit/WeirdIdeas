from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.category_service import create_category

client = TestClient(app)


def test_create_lobby_with_category():
    # register user
    client.post('/auth/register', json={"username": "hostcat", "password": "pw"})
    r = client.post('/auth/login', json={"username": "hostcat", "password": "pw"})
    token = r.json()['access_token']

    # create category
    c = create_category('TestCat', 'desc')

    headers = {"Authorization": f"Bearer {token}"}
    r2 = client.post('/lobbies', json={"max_players": 4, "rounds": 1, "host_id": "hostcat", "category": c['id']}, headers=headers)
    assert r2.status_code == 200
    body = r2.json()
    assert body['category'] == c['id']
    assert 'join_code' in body
