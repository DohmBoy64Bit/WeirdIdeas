"""
Game constants and configuration values.
Centralized location for magic numbers and game rules.
"""

# Combat Constants
REVIVE_HP_PERCENT = 0.5  # Players revive with 50% HP after death
FLEE_SUCCESS_CHANCE = 0.5  # 50% chance to flee successfully
VITALIS_REGEN_PERCENT = 0.05  # Vitalis race regenerates 5% max HP per round
GLACIAL_ICE_ARMOR_REDUCTION = 0.10  # Glacial race reduces damage by 10%
ZENKAI_BATTLE_HARDENED_MAX = 50  # Maximum STR bonus percentage for Zenkai
ZENKAI_BATTLE_HARDENED_INCREMENT = 5  # STR bonus increment per win

# Flux Constants
FLUX_REGEN_PERCENT = 0.10  # 10% of max flux regenerated per combat round
BASE_FLUX = 100  # Base flux for races without specific base_flux
FLUX_PER_INT = 5  # Flux = base_flux + (INT * FLUX_PER_INT)

# Experience Constants
EXP_PER_LEVEL = 100  # Experience required per level (level * EXP_PER_LEVEL)

# Input Validation
MAX_COMMAND_LENGTH = 1000  # Maximum length of WebSocket commands

# Damage Calculation
DAMAGE_VARIANCE_MIN = 0.9  # Minimum damage variance (90%)
DAMAGE_VARIANCE_MAX = 1.1  # Maximum damage variance (110%)

# Level Up Rewards
WISH_LEVEL_BONUS = 5  # Levels gained from using wish command

