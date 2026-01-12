import time
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_game_flow_and_guess():
    # register host and player
    client.post('/auth/register', json={"username": "hostws", "password": "pw"})
    r = client.post('/auth/login', json={"username": "hostws", "password": "pw"})
    host_token = r.json()['access_token']

    client.post('/auth/register', json={"username": "p1", "password": "pw"})
    r2 = client.post('/auth/login', json={"username": "p1", "password": "pw"})
    p1_token = r2.json()['access_token']

    # host creates lobby
    headers = {"Authorization": f"Bearer {host_token}"}
    r3 = client.post('/lobbies', json={"max_players": 4, "rounds": 1, "host_id": "hostws"}, headers=headers)
    lobby = r3.json()
    join_code = lobby['join_code']

    # p1 joins by code
    join_payload = {"join_code": join_code, "player": {"id": "p1", "username": "p1", "display_name": "P1"}}
    r4 = client.post('/lobbies/join_by_code', json=join_payload)
    assert r4.status_code == 200

    # connect websockets using context managers to avoid testclient internal issues
    found = False
    with client.websocket_connect(f"/ws?token={host_token}&lobby={lobby['id']}") as ws_host:
        with client.websocket_connect(f"/ws?token={p1_token}&lobby={lobby['id']}") as ws_p1:
            # consume any initial broadcasts
            for _ in range(3):
                try:
                    ws_host.receive_json(timeout=0.05)
                except Exception:
                    break
            # host starts game via websocket
            ws_host.send_json({"type": "start_game", "data": {"player": {"id": "hostws", "username": "hostws"}}})
            # small delay to allow server to process and broadcast
            time.sleep(0.2)

            # wait until a Game has been created server-side (robust to websocket delivery timing)
            from backend.app.services.game_service import GAMES, RUNTIME
            game = None
            for _ in range(20):
                for g in GAMES.values():
                    if g.lobby_id == lobby['id']:
                        game = g
                        break
                if game:
                    break
                time.sleep(0.05)

            assert game is not None

            # quick submit correct guess (correct_answer is image_0)
            ws_p1.send_json({"type": "submit_guess", "data": {"player_id": "p1", "text": "image_0"}})

            # give server a moment to process the guess
            time.sleep(0.1)

            # verify scores were updated in runtime
            runtime = RUNTIME.get(game.id, {})
            scores = runtime.get('scores', {})
    assert 'p1' in scores
