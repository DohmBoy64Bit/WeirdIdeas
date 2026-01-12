# Pixolve configuration constants (MVP)

# Scoring
MAX_POINTS_PER_ROUND = 1000
MIN_POINTS_PER_ROUND = 100
# If decay_curve is 'linear' we linearly interpolate between MAX and MIN over the round duration
DECAY_CURVE = 'linear'

# Token
TOKEN_DEFAULT_DAYS = 7

# XP & Leveling
LEVEL_BASE_XP = 100  # XP required for level 1->2, increases linearly (level * LEVEL_BASE_XP)

# Game
DEFAULT_ROUND_DURATION = 20  # seconds
DEFAULT_PIXEL_STEPS = [32, 16, 8, 4, 0]