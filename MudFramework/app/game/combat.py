import json
import os
import random
from typing import Dict, Optional

class Mob:
    def __init__(self, data: Dict):
        self.id = data["id"]
        self.name = data["name"]
        self.description = data["description"]
        self.stats = data["stats"].copy() # Copy so instances don't share HP
        self.drops = data.get("drops", [])

class CombatSystem:
    def __init__(self, manager):
        self.manager = manager
        self.mobs_data: Dict[str, Dict] = {}
        self.load_mobs()

    def load_mobs(self):
        base_path = os.path.dirname(os.path.abspath(__file__))
        data_path = os.path.join(base_path, "data", "mobs.json")
        try:
            with open(data_path, "r") as f:
                self.mobs_data = json.load(f)
        except Exception as e:
            print(f"Error loading mobs: {e}")

    def spawn_mob(self, mob_id: str) -> Optional[Mob]:
        data = self.mobs_data.get(mob_id)
        if data:
            return Mob(data)
        return None

    def calculate_damage(self, attacker_stats: Dict, defender_stats: Dict) -> int:
        # Simple formula: Damage = STR * 2 - VIT
        dmg = (attacker_stats.get("str", 0) * 2) - defender_stats.get("vit", 0)
        # Random variance +/- 10%
        variance = random.uniform(0.9, 1.1)
        final_dmg = int(max(1, dmg) * variance)
        return final_dmg

    async def combat_round(self, player, mob: Mob, action: str):
        # 1. Player Action
        results = []
        player_dmg = 0
        
        if action == "attack":
            player_dmg = self.calculate_damage(player.stats, mob.stats)
            mob.stats["hp"] -= player_dmg
            results.append(f"You hit {mob.name} for {player_dmg} damage!")
        else:
             results.append(f"You perform {action}...")

        # Check Mob Death
        if mob.stats["hp"] <= 0:
            results.append(f"{mob.name} is defeated!")
            results.append(f"You gain {mob.stats['exp']} EXP.")
            
            loot = []
            for drop in mob.drops:
                if random.random() < drop["rate"]:
                    loot.append(drop["item_id"])
                    
            return {"status": "win", "log": results, "exp": mob.stats["exp"], "loot": loot}

        # 2. Mob Action
        mob_dmg = self.calculate_damage(mob.stats, player.stats)
        # We need to update player HP in DB technically, but for now let's just calc it
        # Real system would persist HP. Assuming player.stats has "hp" or "current_hp"
        
        current_hp = player.stats.get("hp", 100)
        current_hp -= mob_dmg
        player.stats["hp"] = current_hp
        results.append(f"{mob.name} attacks you for {mob_dmg} damage!")

        if current_hp <= 0:
             results.append("You have been defeated...")
             return {"status": "loss", "log": results}

        return {"status": "continue", "log": results, "mob_hp": mob.stats["hp"], "player_hp": current_hp}
