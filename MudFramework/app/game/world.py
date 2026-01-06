import json
import os
from typing import Dict, Optional, List

class Room:
    def __init__(self, data: Dict):
        self.id = data["id"]
        self.name = data["name"]
        self.description = data["description"]
        self.exits: Dict[str, str] = data.get("exits", {}) # dir -> room_id
        self.mobs: List[str] = data.get("mobs", []) # mob_ids

class World:
    def __init__(self):
        self.rooms: Dict[str, Room] = {}
        self.load_rooms()

    def load_rooms(self):
        # Path relative to this file
        base_path = os.path.dirname(os.path.abspath(__file__))
        data_path = os.path.join(base_path, "data", "rooms.json")
        
        try:
            with open(data_path, "r") as f:
                data = json.load(f)
                for room_id, room_data in data.items():
                    self.rooms[room_id] = Room(room_data)
            print(f"Loaded {len(self.rooms)} rooms.")
        except Exception as e:
            print(f"Error loading rooms: {e}")

    def get_room(self, room_id: str) -> Optional[Room]:
        return self.rooms.get(room_id)

    def get_start_room(self) -> Room:
        return self.rooms.get("start_area") or list(self.rooms.values())[0]

# Singleton instance
world = World()
