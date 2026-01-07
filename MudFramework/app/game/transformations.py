from typing import Dict, Optional

# Definitions for transformations (name -> multiplier / reqs)
# Simplified for now.
TRANSFORMATIONS = {
    # Zenkai
    "Super Zenkai": {"req_level": 5, "mult": 1.5, "race": "Zenkai"},
    "Super Zenkai 2": {"req_level": 10, "mult": 2.0, "race": "Zenkai"},
    "God Zenkai": {"req_level": 20, "mult": 5.0, "race": "Zenkai"},
    
    # Vitalis
    "Giant Vitalis": {"req_level": 5, "mult": 1.5, "race": "Vitalis"},
    "Awakened Vitalis": {"req_level": 15, "mult": 3.0, "race": "Vitalis"},
    
    # Terran
    "Unlock Potential": {"req_level": 5, "mult": 1.3, "race": "Terran"},
    "High Tension": {"req_level": 10, "mult": 1.8, "race": "Terran"},
    
    # Glacial
    "Second Form": {"req_level": 5, "mult": 1.4, "race": "Glacial"},
    "Third Form": {"req_level": 10, "mult": 1.8, "race": "Glacial"},
    "Final Form": {"req_level": 15, "mult": 2.5, "race": "Glacial"},
    "Golden Form": {"req_level": 25, "mult": 5.0, "race": "Glacial"},
}

def get_transformation(name: str) -> Optional[Dict]:
    return TRANSFORMATIONS.get(name)

def get_available_transformations(race: str, level: int) -> list:
    return [name for name, data in TRANSFORMATIONS.items() 
            if data["race"] == race and level >= data["req_level"]]

def calculate_effective_stats(base_stats, transformation_name="Base"):
    """Apply transformation multipliers to base stats and passives."""
    if transformation_name == "Base":
        return base_stats.copy()
    
    transformation = get_transformation(transformation_name)
    if not transformation:
        return base_stats.copy()
    
    effective = {}
    # The original TRANSFORMATIONS structure uses a single 'mult' key.
    # This logic assumes a 'multipliers' dictionary within the transformation data.
    # For this change, we'll adapt to the existing 'mult' key for general stats
    # and assume 'multipliers' might be added later or is implied for specific stats.
    # If 'multipliers' is not present, it will fall back to the general 'mult'.
    
    general_mult = transformation.get("mult", 1.0) # Default to 1.0 if no general multiplier
    
    for stat, value in base_stats.items():
        # Check if there's a specific multiplier for this stat
        if "multipliers" in transformation and stat in transformation["multipliers"]:
            effective[stat] = int(value * transformation["multipliers"][stat])
        elif isinstance(value, (int, float)): # Apply general multiplier if it's a numeric stat
            effective[stat] = int(value * general_mult)
        else:
            effective[stat] = value
    
    # Apply Zenkai: Battle Hardened passive (STR bonus)
    if "battle_hardened_bonus" in base_stats:
        bonus_percent = base_stats["battle_hardened_bonus"]
        if "str" in effective:
            str_bonus = int(effective["str"] * (bonus_percent / 100))
            effective["str"] += str_bonus
    
    return effective
