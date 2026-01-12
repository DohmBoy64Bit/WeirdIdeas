from backend.app.services.scoring import compute_points


def test_full_points_at_start():
    assert compute_points(0, 20) == 1000


def test_min_points_at_end():
    assert compute_points(20, 20) == 100


def test_mid_points():
    p = compute_points(10, 20)
    assert 100 < p < 1000
