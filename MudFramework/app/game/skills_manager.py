import json
import os
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class Skill:
    def __init__(self, data: Dict):
        self.id = data["id"]
        self.name = data["name"]
        self.type = data["type"]
        self.race_required = data.get("race_required")
        self.description = data["description"]
        self.level_required = data["level_required"]
        self.flux_cost = data.get("flux_cost", 0)  # Flux cost to use skill
        self.cooldown = data.get("cooldown", 0)  # Cooldown in rounds
        
        # Damage/healing
        self.damage_multiplier = data.get("damage_multiplier", 0)
        self.stat_type = data.get("stat_type", "str")
        self.heal_percent = data.get("heal_percent", 0)
        
        # Special effects
        self.ignores_defense = data.get("ignores_defense", False)
        self.defense_pierce_percent = data.get("defense_pierce_percent", 0)
        self.skip_enemy_turn = data.get("skip_enemy_turn", False)
        self.guaranteed_hit = data.get("guaranteed_hit", False)
        self.dodge_chance = data.get("dodge_chance", 0)
        
        # Buffs/debuffs
        self.self_debuff = data.get("self_debuff", 1.0)
        self.hp_cost_percent = data.get("hp_cost_percent", 0)
        self.damage_reduction = data.get("damage_reduction", 0)
        self.buff_stat = data.get("buff_stat")
        self.buff_percent = data.get("buff_percent", 0)
        self.buff_duration = data.get("buff_duration", 0)
        
        # Requirements
        self.transformation_required = data.get("transformation_required")
        self.skip_attack = data.get("skip_attack", False)

class SkillsManager:
    def __init__(self):
        self.skills: Dict[str, Skill] = {}
        self.load_skills()

    def load_skills(self):
        base_path = os.path.dirname(os.path.abspath(__file__))
        data_path = os.path.join(base_path, "data", "skills.json")
        
        try:
            with open(data_path, "r") as f:
                data = json.load(f)
                for skill_id, skill_data in data.items():
                    self.skills[skill_id] = Skill(skill_data)
            logger.info(f"Loaded {len(self.skills)} skills.")
        except Exception as e:
            logger.error(f"Error loading skills: {e}", exc_info=True)

    def get_skill(self, skill_id: str) -> Optional[Skill]:
        return self.skills.get(skill_id)

    def get_skill_by_name(self, name: str) -> Optional[Skill]:
        """Get skill by name (case-insensitive)."""
        for skill in self.skills.values():
            if skill.name.lower() == name.lower():
                return skill
        return None

    def get_available_skills(self, race: str, level: int) -> List[Skill]:
        """Get all skills that a player can learn based on race and level."""
        available = []
        for skill in self.skills.values():
            # Check level requirement
            if level < skill.level_required:
                continue
            
            # Check race requirement (None means general skill)
            if skill.race_required and skill.race_required != race:
                continue
                
            available.append(skill)
        
        return available

    def get_all_race_skills(self, race: str) -> List[Skill]:
        """Get ALL skills for a race, regardless of level."""
        relevant = []
        for skill in self.skills.values():
            if skill.race_required and skill.race_required != race:
                continue
            relevant.append(skill)
        return sorted(relevant, key=lambda x: x.level_required)

    def get_race_passive(self, race: str) -> Dict:
        """Get passive ability for a race."""
        passives = {
            "Zenkai": {
                "name": "Battle Hardened",
                "description": "Gain +5% STR per combat won (max 50%, resets on death)"
            },
            "Vitalis": {
                "name": "Regeneration",
                "description": "Restore 5% max HP at start of each combat round"
            },
            "Terran": {
                "name": "Tactical Mind",
                "description": "+10% damage to enemies you've fought before"
            },
            "Glacial": {
                "name": "Ice Armor",
                "description": "Reduce all incoming damage by 10%"
            }
        }
        return passives.get(race, {"name": "None", "description": "No passive ability"})

    def can_use_skill(self, skill_id: str, player_race: str, player_level: int, player_transformation: str = "Base") -> tuple[bool, str]:
        """Check if player can use a skill. Returns (can_use, error_message)"""
        skill = self.get_skill(skill_id)
        if not skill:
            return False, "Skill not found."
        
        if player_level < skill.level_required:
            return False, f"Requires level {skill.level_required}."
        
        if skill.race_required and skill.race_required != player_race:
            return False, f"This skill is only for {skill.race_required} race."
        
        if skill.transformation_required and skill.transformation_required != player_transformation:
            return False, f"Requires {skill.transformation_required} transformation."
        
        return True, ""

# Singleton
skills_manager = SkillsManager()
