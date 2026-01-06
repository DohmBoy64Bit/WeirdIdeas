from app.core.database import SessionLocal
from app.models.race import Race

def seed_races():
    db = SessionLocal()
    races = [
        {
            "name": "Zenkai",
            "description": "A warrior race that grows stronger after every battle.",
            "base_stats": {"str": 10, "dex": 5, "int": 3, "vit": 8},
            "scaling_stats": {"str": 2.0, "dex": 1.0, "int": 0.5, "vit": 1.5},
            "transformations": ["Super Zenkai", "Super Zenkai 2", "God Zenkai"]
        },
        {
            "name": "Vitalis",
            "description": "A mystical race with high regeneration and magic.",
            "base_stats": {"str": 4, "dex": 5, "int": 10, "vit": 10},
            "scaling_stats": {"str": 0.5, "dex": 1.0, "int": 2.0, "vit": 2.0},
            "transformations": ["Giant Vitalis", "Awakened Vitalis"]
        },
        {
            "name": "Terran",
            "description": "Resourceful and balanced, adept at using technology.",
            "base_stats": {"str": 6, "dex": 6, "int": 6, "vit": 6},
            "scaling_stats": {"str": 1.2, "dex": 1.2, "int": 1.2, "vit": 1.2},
            "transformations": ["Unlock Potential", "High Tension"]
        },
        {
            "name": "Glacial",
            "description": "A durable race capable of multiple physical forms.",
            "base_stats": {"str": 8, "dex": 8, "int": 4, "vit": 8},
            "scaling_stats": {"str": 1.5, "dex": 1.5, "int": 0.8, "vit": 1.5},
            "transformations": ["Second Form", "Third Form", "Final Form", "Golden Form"]
        },
    ]

    for r in races:
        existing = db.query(Race).filter(Race.name == r["name"]).first()
        if not existing:
            race_obj = Race(**r)
            db.add(race_obj)
            print(f"Added race: {r['name']}")
    
    db.commit()
    db.close()

if __name__ == "__main__":
    seed_races()
