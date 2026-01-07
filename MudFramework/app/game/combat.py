import json
import os
import random
from typing import Dict, Optional
from app.game.skills_manager import skills_manager, Skill

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

    def calculate_damage(self, attacker_stats: Dict, defender_stats: Dict, defense_pierce: int = 0) -> int:
        # Simple formula: Damage = STR * 2 - VIT
        vit = defender_stats.get("vit", 0)
        if defense_pierce > 0:
            vit = int(vit * (1 - defense_pierce / 100))
        dmg = (attacker_stats.get("str", 0) * 2) - vit
        # Random variance +/- 10%
        variance = random.uniform(0.9, 1.1)
        final_dmg = int(max(1, dmg) * variance)
        return final_dmg

    def calculate_skill_damage(self, player_stats: Dict, skill: Skill) -> int:
        """Calculate damage for a skill."""
        if skill.stat_type == "str":
            base = player_stats.get("str", 0)
        elif skill.stat_type == "int":
            base = player_stats.get("int", 0)
        elif skill.stat_type == "str_dex":
            base = player_stats.get("str", 0) + player_stats.get("dex", 0)
        else:
            base = player_stats.get("str", 0)
        
        dmg = int(base * skill.damage_multiplier)
        variance = random.uniform(0.9, 1.1)
        return int(dmg * variance)

    async def combat_round(self, player, mob: Mob, action: str, skill: Optional[Skill] = None):
        # Apply passive abilities at start of round
        results = []
        player_race = getattr(player, 'race', None)
        
        # Vitalis: Regeneration - 5% max HP at start of round
        if player_race == "Vitalis":
            max_hp = player.stats.get("max_hp", 100)
            regen = int(max_hp * 0.05)
            player.stats["hp"] = min(max_hp, player.stats["hp"] + regen)
            results.append(f"[Regeneration] You recover {regen} HP!")
        
        # 1. Player Action
        player_dmg = 0
        skip_mob_attack = False
        
        if skill:
            # Using a skill
            if skill.heal_percent > 0:
                heal = int(player.stats.get("max_hp", 100) * skill.heal_percent / 100)
                player.stats["hp"] = min(player.stats["max_hp"], player.stats["hp"] + heal)
                results.append(f"You used {skill.name} and recovered {heal} HP!")
            
            if skill.damage_multiplier > 0 and not skill.skip_attack:
                if skill.ignores_defense:
                    player_dmg = self.calculate_skill_damage(player.stats, skill)
                else:
                    player_dmg = self.calculate_skill_damage(player.stats, skill)
                    if skill.defense_pierce_percent > 0:
                        # Reduce effectiveness of mob VIT
                        vit_mod = mob.stats.get("vit", 0) * (skill.defense_pierce_percent / 100)
                        player_dmg -= int(vit_mod)
                
                if skill.hp_cost_percent > 0:
                    hp_cost = int(player.stats["hp"] * skill.hp_cost_percent / 100)
                    player.stats["hp"] -= hp_cost
                    results.append(f"You sacrificed {hp_cost} HP!")
                
                mob.stats["hp"] -= player_dmg
                results.append(f"You used {skill.name} and dealt {player_dmg} damage!")
            
            if skill.skip_enemy_turn:
                skip_mob_attack = True
                results.append(f"{mob.name} is frozen in time!")
            
            if skill.damage_reduction > 0:
                results.append(f"You activate {skill.name}! Damage reduced this round.")
        elif action == "attack":
            player_dmg = self.calculate_damage(player.stats, mob.stats)
            
            # Terran: Tactical Mind - track defeated mobs for bonus damage
            # (Would need mob tracking in player stats - simplified for now)
            
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

        # 2. Mob Action (if not skipped)
        if not skip_mob_attack:
            mob_dmg = self.calculate_damage(mob.stats, player.stats)
            
            # Apply damage reduction if skill used
            if skill and skill.damage_reduction > 0:
                mob_dmg = int(mob_dmg * (1 - skill.damage_reduction))
                results.append(f"Your shield absorbs some damage!")
            
            # Glacial: Ice Armor - 10% damage reduction
            if player_race == "Glacial":
                ice_reduction = int(mob_dmg * 0.10)
                mob_dmg -= ice_reduction
                results.append(f"[Ice Armor] Reduced damage by {ice_reduction}!")
            
            current_hp = player.stats.get("hp", 100)
            current_hp -= mob_dmg
            player.stats["hp"] = current_hp
            results.append(f"{mob.name} attacks you for {mob_dmg} damage!")

            if current_hp <= 0:
                 results.append("You have been defeated...")
                 return {"status": "loss", "log": results}

        return {"status": "continue", "log": results, "mob_hp": mob.stats["hp"], "player_hp": player.stats.get("hp", 100)}
