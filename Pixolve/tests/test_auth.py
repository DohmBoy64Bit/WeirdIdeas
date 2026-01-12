from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_register_and_login():
    # register
    r = client.post('/auth/register', json={"username": "tester", "password": "secret"})
    assert r.status_code == 200
    body = r.json()
    assert body['username'] == 'tester'

    # login
    r2 = client.post('/auth/login', json={"username": "tester", "password": "secret"})
    assert r2.status_code == 200
    t = r2.json()
    assert 'access_token' in t


def test_invalid_login():
    r = client.post('/auth/login', json={"username": "noone", "password": "x"})
    assert r.status_code == 401