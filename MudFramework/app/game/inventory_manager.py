import json
import os
from typing import Dict, Optional, List

class Item:
    def __init__(self, data: Dict):
        self.id = data["id"]
        self.name = data["name"]
        self.type = data["type"]
        self.description = data["description"]
        self.price = data.get("price", 0)
        self.effect = data.get("effect", {}) # For consumables
        self.stats = data.get("stats", {}) # For equipment

class InventoryManager:
    def __init__(self):
        self.items: Dict[str, Item] = {}
        self.shops: Dict[str, Dict] = {}
        self.load_data()

    def load_data(self):
        base_path = os.path.dirname(os.path.abspath(__file__))
        
        # Load Items
        try:
            with open(os.path.join(base_path, "data", "items.json"), "r") as f:
                data = json.load(f)
                for k, v in data.items():
                    self.items[k] = Item(v)
        except Exception as e:
            print(f"Error loading items: {e}")

        # Load Shops
        try:
            with open(os.path.join(base_path, "data", "shops.json"), "r") as f:
                self.shops = json.load(f)
        except Exception as e:
             print(f"Error loading shops: {e}")

    def get_item(self, item_id: str) -> Optional[Item]:
        return self.items.get(item_id)

    def get_shop(self, shop_id: str) -> Optional[Dict]:
        return self.shops.get(shop_id)

inventory_manager = InventoryManager()
