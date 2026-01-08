import json
import os
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class QuestManager:
    def __init__(self):
        self.npcs: Dict = {}
        self.quests: Dict = {}
        self.load_data()

    def load_data(self):
        base_path = os.path.dirname(os.path.abspath(__file__))
        
        # Load NPCs
        try:
            with open(os.path.join(base_path, "data", "npcs.json"), "r") as f:
                self.npcs = json.load(f)
            logger.info(f"Loaded {len(self.npcs)} NPCs.")
        except Exception as e:
            logger.error(f"Error loading NPCs: {e}", exc_info=True)

        # Load Quests
        try:
            with open(os.path.join(base_path, "data", "quests.json"), "r") as f:
                self.quests = json.load(f)
            logger.info(f"Loaded {len(self.quests)} quests.")
        except Exception as e:
            logger.error(f"Error loading Quests: {e}", exc_info=True)

    def get_npc_by_room(self, room_id: str) -> Optional[Dict]:
        for npc in self.npcs.values():
            if npc["room_id"] == room_id:
                return npc
        return None

    def get_quest(self, quest_id: str) -> Optional[Dict]:
        return self.quests.get(quest_id)

quest_manager = QuestManager()
