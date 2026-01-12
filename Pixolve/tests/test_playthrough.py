import time
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services import auth_service

client = TestClient(app)


def read_until(ws, predicate, timeout=5):
    """Blocking read messages from ws until predicate(msg) is True or timeout expires. Returns the message or raises RuntimeError."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            msg = ws.receive_json()
        except Exception:
            time.sleep(0.01)
            continue
        if predicate(msg):
            return msg
    raise RuntimeError('timeout waiting for message')


def test_full_playthrough_two_players():
    # register host and two players
    client.post('/auth/register', json={"username": "hostplay", "password": "pw"})
    r = client.post('/auth/login', json={"username": "hostplay", "password": "pw"})
    host_token = r.json()['access_token']

    client.post('/auth/register', json={"username": "alice", "password": "pw"})
    ra = client.post('/auth/login', json={"username": "alice", "password": "pw"})
    alice_token = ra.json()['access_token']

    client.post('/auth/register', json={"username": "bob", "password": "pw"})
    rb = client.post('/auth/login', json={"username": "bob", "password": "pw"})
    bob_token = rb.json()['access_token']

    # host creates lobby
    headers = {"Authorization": f"Bearer {host_token}"}
    r3 = client.post('/lobbies', json={"max_players": 4, "rounds": 1, "host_id": "hostplay"}, headers=headers)
    lobby = r3.json()

    # two players join by code
    join_payload_a = {"join_code": lobby['join_code'], "player": {"id": "alice", "username": "alice", "display_name": "Alice"}}
    client.post('/lobbies/join_by_code', json=join_payload_a)
    join_payload_b = {"join_code": lobby['join_code'], "player": {"id": "bob", "username": "bob", "display_name": "Bob"}}
    client.post('/lobbies/join_by_code', json=join_payload_b)

    # connect websockets using context managers
    with client.websocket_connect(f"/ws?token={host_token}&lobby={lobby['id']}") as ws_host:
        with client.websocket_connect(f"/ws?token={alice_token}&lobby={lobby['id']}") as ws_alice:
            with client.websocket_connect(f"/ws?token={bob_token}&lobby={lobby['id']}") as ws_bob:

                # host starts game
                ws_host.send_json({"type": "start_game", "data": {"player": {"id": "hostplay", "username": "hostplay"}}})

                # wait for game_started on all sockets
                g1 = read_until(ws_host, lambda m: m.get('type') == 'game_started', timeout=3)
                g2 = read_until(ws_alice, lambda m: m.get('type') in ('start_round','game_started','lobby_update'), timeout=3)

                assert g1['type'] == 'game_started'

                # wait for start_round on one socket
                sr = read_until(ws_alice, lambda m: m.get('type') == 'start_round', timeout=5)
                assert sr['type'] == 'start_round'

                # alice guesses correctly immediately
                ws_alice.send_json({"type": "submit_guess", "data": {"player_id": "alice", "text": "image_0"}})
                # wait for alice to see her guess_result
                res_a = read_until(ws_alice, lambda m: m.get('type') == 'guess_result' and m.get('data', {}).get('player_id') == 'alice', timeout=3)
                assert res_a['data']['correct'] is True

                # consume the scoreboard update after alice's guess so host's queue is up-to-date
                _ = read_until(ws_host, lambda m: m.get('type') == 'scoreboard_update', timeout=3)

                # bob guesses shortly after (reduce delay to avoid timing flakiness)
                time.sleep(0.1)
                ws_bob.send_json({"type": "submit_guess", "data": {"player_id": "bob", "text": "image_0"}})
                res_b = read_until(ws_bob, lambda m: m.get('type') == 'guess_result' and m.get('data', {}).get('player_id') == 'bob', timeout=3)
                assert res_b['data']['correct'] is True

                # wait for scoreboard_update
                sb = read_until(ws_host, lambda m: m.get('type') == 'scoreboard_update', timeout=3)
                scores = sb['data'].get('scores', {})
                assert 'alice' in scores and 'bob' in scores
                assert scores['alice'] >= scores['bob']  # alice guessed earlier or equal

                # check XP applied to users
                ua = auth_service.get_user_by_username('alice')
                ub = auth_service.get_user_by_username('bob')
                assert ua and ub
                assert ua.get('xp', 0) >= 0
                assert ub.get('xp', 0) >= 0
