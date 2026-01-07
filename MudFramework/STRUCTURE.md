# MUD Framework - File Structure

## Core Application
```
app/
├── api/                  # API endpoints
│   ├── endpoints/       # Route handlers
│   └── deps.py         # Dependencies
├── core/               # Core configuration
│   ├── config.py       # Settings
│   ├── database.py     # Database setup
│   └── security.py     # Auth utilities
├── game/               # Game logic
│   ├── data/           # Game data (JSON)
│   ├── combat.py       # Combat system
│   ├── engine.py       # Game engine
│   ├── inventory_manager.py
│   ├── quest_manager.py
│   ├── skills_manager.py
│   └── transformations.py
├── models/             # Database models
│   ├── player.py
│   ├── race.py
│   └── user.py
├── schemas/            # Pydantic schemas
│   ├── player.py
│   ├── race.py
│   └── user.py
├── websockets/         # WebSocket handlers
│   └── connection_manager.py
└── main.py            # FastAPI app

## Frontend
templates/              # HTML templates
static/                # CSS/JS/Images

## Database
alembic/               # Database migrations
mud.db                 # SQLite database

## Configuration
alembic.ini            # Alembic config
seed_data.py           # Initial data seeding
MIGRATIONS.md          # Migration guide
README.md              # Project documentation
```

## Temporary/Development Files (Cleaned)
- ❌ test_*.py files (manual test scripts)
- ❌ add_skills_column.py (database patch)
- ❌ add_flux_column.py (database patch)
- ❌ update_race_flux.py (database patch)

All database changes should now use Alembic migrations instead of manual scripts.
