from backend.app.services import auth_service
from backend.app.api.lobbies import _LOBBIES
from backend.app.services.game_service import start_game_for_lobby, process_guess_for_lobby, RUNTIME
from datetime import datetime, timedelta, timezone


def test_process_guess_awards_points_and_xp():
    # create user
    u = auth_service.create_user('gtester','pw','G Tester')
    username = 'gtester'

    # create a lobby with that player already in players list
    lobby_id = 'lobby-test'
    from backend.app.schemas.lobby import LobbyOut, PlayerInLobby
    p = PlayerInLobby(id=username, username=username, display_name='G')
    lobby = LobbyOut(id=lobby_id, host_id=username, max_players=4, players=[p], category=None, rounds=1, join_code='CODE')
    _LOBBIES[lobby_id] = lobby

    # start game
    gs = start_game_for_lobby(lobby_id)
    gid = gs.id
    # set runtime started
    RUNTIME[gid]['round_started_at'] = datetime.now(timezone.utc) - timedelta(seconds=1)
    RUNTIME[gid]['current_round_index'] = 0

    # submit correct guess
    res = process_guess_for_lobby(lobby_id, username, gs.rounds[0].correct_answer)
    assert res['correct'] is True
    assert res['points_awarded'] > 0
    assert res['xp_awarded'] == res['points_awarded'] // 10

    # verify XP added to user
    u2 = auth_service.get_user_by_username(username)
    assert u2 is not None
    assert u2.get('xp', 0) >= res['xp_awarded']


def test_double_guess_prevented():
    u = auth_service.create_user('gtester2','pw','G2')
    username = 'gtester2'
    lobby_id = 'lobby-test-2'
    from backend.app.schemas.lobby import LobbyOut, PlayerInLobby
    p = PlayerInLobby(id=username, username=username, display_name='G2')
    lobby = LobbyOut(id=lobby_id, host_id=username, max_players=4, players=[p], category=None, rounds=1, join_code='CODE2')
    _LOBBIES[lobby_id] = lobby
    gs = start_game_for_lobby(lobby_id)
    gid = gs.id
    RUNTIME[gid]['round_started_at'] = datetime.now(timezone.utc) - timedelta(seconds=1)
    RUNTIME[gid]['current_round_index'] = 0

    res1 = process_guess_for_lobby(lobby_id, username, gs.rounds[0].correct_answer)
    assert res1['correct'] is True
    res2 = process_guess_for_lobby(lobby_id, username, gs.rounds[0].correct_answer)
    assert res2['correct'] is False
    assert res2.get('reason') == 'already_correct'