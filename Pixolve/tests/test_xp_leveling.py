from backend.app.services import auth_service


def test_add_xp_and_level_up():
    u = auth_service.create_user('xpuser','pw','XP User')
    username = 'xpuser'
    # add 150 xp -> should level from 1 to 2 (threshold 100)
    auth_service.add_xp(username, 150)
    u2 = auth_service.get_user_by_username(username)
    assert u2['xp'] >= 150
    assert u2['level'] >= 2

    # add enough xp to reach multiple levels
    auth_service.add_xp(username, 500)
    u3 = auth_service.get_user_by_username(username)
    assert u3['level'] >= 3
