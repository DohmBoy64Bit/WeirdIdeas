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

def calculate_effective_stats(player_stats: Dict, transformation: str) -> Dict:
    data = TRANSFORMATIONS.get(transformation)
    if not data:
        return player_stats.copy()

    mult = data["mult"]
    new_stats = {}
    for k, v in player_stats.items():
        if isinstance(v, (int, float)):
             new_stats[k] = int(v * mult)
        else:
             new_stats[k] = v
    return new_stats
