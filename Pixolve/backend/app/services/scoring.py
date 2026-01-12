from math import floor
from ..config import MAX_POINTS_PER_ROUND, MIN_POINTS_PER_ROUND


def compute_points(time_elapsed: float, round_duration: float) -> int:
    """Compute points based on time elapsed in the round. Returns an int between MIN_POINTS_PER_ROUND and MAX_POINTS_PER_ROUND."""
    if time_elapsed <= 0:
        return MAX_POINTS_PER_ROUND
    frac = min(max(time_elapsed / round_duration, 0.0), 1.0)
    # linear decay: early guesses get more points
    points = MAX_POINTS_PER_ROUND - frac * (MAX_POINTS_PER_ROUND - MIN_POINTS_PER_ROUND)
    return int(floor(points))
