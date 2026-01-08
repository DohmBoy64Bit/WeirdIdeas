# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Commands

### Install dependencies

```bash
python -m pip install -r requirements.txt
```

### Run the FastAPI app (development)

The main ASGI app is defined in `app/main.py` as a FastAPI application.

```bash
uvicorn app.main:app --reload
```

By default, the app uses SQLite at `mud.db` configured via `app/core/config.py`.

### Database setup and maintenance

Database configuration and session management live in `app/core/database.py`. The project uses SQLAlchemy models and Alembic migrations.

**Initial DB schema (if starting from scratch):**

```bash
python create_db.py
```

This script imports models from `app.models.*` and calls `Base.metadata.create_all` against the configured engine.

**Seed core game data (races):**

```bash
python seed_data.py
```

**Clean player/user data in the local SQLite DB:**

```bash
python clean_db.py
```

This deletes all rows from the `users` and `players` tables in `mud.db` and prints resulting counts.

### Alembic migrations

Schema changes should go through Alembic. The key workflow (also documented in `MIGRATIONS.md`) is:

- Create a migration after changing SQLAlchemy models in `app/models/*`:

  ```bash
  alembic revision --autogenerate -m "Description of change"
  ```

- Apply latest migrations:

  ```bash
  alembic upgrade head
  ```

- Roll back the last migration:

  ```bash
  alembic downgrade -1
  ```

- View history / current revision:

  ```bash
  alembic history
  alembic current
  ```

See `MIGRATIONS.md` for additional troubleshooting notes and examples.

### Running tests

Pytest is configured via `pytest.ini` with tests under `tests/`.

**All tests:**

```bash
python -m pytest tests/ -v
```

**Single test file:**

```bash
python -m pytest tests/test_flux_comprehensive.py -v
```

**Single test class:**

```bash
python -m pytest tests/test_races.py::TestAllRaces -v
```

**Single test function:**

```bash
python -m pytest tests/test_auth.py::TestAuthentication::test_signup -v
```

**With coverage report for the app package:**

```bash
python -m pytest tests/ --cov=app --cov-report=html
```

Pytest markers available (from `pytest.ini`):

- `slow` – slow tests
- `integration` – tests that require the server running

## High-level architecture

### Overview

This repository implements a FastAPI-based MUD (multi-user dungeon) framework with a WebSocket-driven game loop, a REST API for authentication and character management, and a game engine that orchestrates combat, movement, quests, inventory, and progression.

At a high level:

- `app/main.py` wires together the FastAPI app, CORS, rate limiting, static/template serving, API routers, and the WebSocket endpoint.
- `app/core/` holds configuration, DB session setup, security helpers, constants, and shared game messages.
- `app/models/` defines SQLAlchemy models for `User`, `Player`, and `Race` (and any future entities) backed by the SQLite database.
- `app/schemas/` defines the Pydantic models that correspond to the HTTP API payloads.
- `app/api/` defines dependency wiring and HTTP routes (e.g. auth, players, races) that sit on top of the models/schemas.
- `app/websockets/` manages connected game clients and handles sending/receiving messages over WebSockets.
- `app/game/` contains the core game engine and systems (world, combat, inventory, quests, skills, transformations) used by the WebSocket command loop.
- `templates/` and `static/` provide the minimal HTML/JS frontend for connecting to the game.

The test suite under `tests/` exercises the end-to-end behaviour of the API and the game engine, including races, skills, flux system, combat, progression, and world features.

### app/core – configuration, DB, and shared concerns

- `app/core/config.py`
  - Uses `pydantic-settings` to load `Settings` from environment variables and `.env`.
  - Provides:
    - `PROJECT_NAME`, `API_V1_STR`, `DATABASE_URL` (defaults to `sqlite:///./mud.db`).
    - JWT-related settings: `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`.
    - CORS origins list for local development frontends.
    - DB pool settings and `DEBUG_MODE` flag (controls dev-only commands in the engine).
- `app/core/database.py`
  - Creates the SQLAlchemy engine from `settings.DATABASE_URL` with `pool_pre_ping` and basic pooling.
  - Exposes `SessionLocal` (DB session factory) and `Base` (declarative base) used by models.
  - Provides `get_db()` dependency generator for FastAPI routes.
- `app/core/security.py` (not shown above but implied by structure)
  - Handles auth helpers (JWT creation/verification, password hashing) used by API endpoints and the WebSocket token flow.
- `app/core/constants.py` and `app/core/messages.py`
  - Central place for gameplay constants (flux, regen %, command length limits, etc.) and user-facing game messages.
  - `MAX_COMMAND_LENGTH` from `constants.py` is enforced in the WebSocket loop.

These modules are imported broadly (e.g. by the game engine, WebSocket handler, and API endpoints), so changes here have cross-cutting impact.

### app/models and app/schemas – persistence and I/O contracts

- `app/models/`
  - `user.py`, `player.py`, `race.py` are SQLAlchemy models attached to `Base` from `app.core.database`.
  - `Player` stores state such as location, stats, flux, inventory, quest progress, and combat state, which the game engine mutates.
  - `Race` defines per-race base stats, scaling, transformations, and base flux; `seed_data.py` inserts canonical race rows.
- `app/schemas/`
  - Mirrors the domain models but expressed as Pydantic models for FastAPI request/response bodies.
  - These schemas form the stable contract for `app/api` endpoints.

When adjusting persistence structure, update models first, then create Alembic migrations, then align schemas and tests.

### app/api – HTTP layer

- `app/api/deps.py`
  - FastAPI dependency functions for DB sessions, current user, and auth-related helpers.
- `app/api/endpoints/`
  - `auth.py` – signup/login/token issuance, character creation, and any auth-related routes. Integrates with rate-limiting when enabled.
  - `players.py` – CRUD and detail endpoints around `Player` entities.
  - `races.py` – endpoints exposing race metadata.
- `app/api/api.py`
  - Assembles the `APIRouter` for versioned API (mounted under `settings.API_V1_STR`, usually `/api/v1`).

The test suite (`tests/test_auth.py`, `tests/test_races.py`, etc.) exercises these HTTP endpoints directly and should be consulted when modifying their behaviour.

### app/websockets – connection management

- `app/websockets/connection_manager.py`
  - Manages active WebSocket connections keyed by player or user.
  - Provides methods to send system/game messages and refresh UI for specific players.

`GameEngine` receives a `connection_manager` instance and uses it to push game state to clients.

### app/game – game engine and systems

- `app/game/engine.py`
  - Central `GameEngine` class that processes text commands from players and orchestrates all subsystems.
  - Entry point `process_command(player_id, command, db)`:
    - Fetches `Player` from DB; returns early if not found.
    - Splits the incoming command into verb and args.
    - If `player.combat_state` is active, routes only combat-related verbs (`attack`, `flee`, `use`, `skill`) and otherwise sends an "in combat" system message.
    - For non-combat state, dispatches verbs to handlers for movement (`look`, directions, `move`), social (`say`), hunting, transformations (`transform`, `revert`), inventory/shops (`inventory`, `shop`, `buy`, `use`), NPC/quests (`talk`, `quests`, `wish`), skills (`skills`, `skillinfo`, `passive`), and a small set of dev-only `cheat_*` commands gated by `settings.DEBUG_MODE`.
  - Integrates with:
    - `CombatSystem` from `app.game.combat` and `Mob` model for encounters.
    - `world` data from `app.game.world` for locations and navigation.
    - `quest_manager` for quest progression.
    - `inventory_manager` and `skills_manager` for manipulating player inventory and skills.
    - Race and transformation utilities (`get_transformation`, `calculate_effective_stats`).
  - Uses `GameMessages` and constants for consistent UX and rule enforcement, and `flag_modified` to mark JSON-like columns (e.g. inventory) as changed before committing.

- Other notable game modules:
  - `combat.py` – turn-based combat rules (attack rounds, damage, flee, death/revive logic).
  - `inventory_manager.py` – item lookup, stacking, and usage.
  - `skills_manager.py` – skill definitions, flux costs, cooldowns.
  - `quest_manager.py` – quest definitions and state transitions.
  - `transformations.py` – race-specific transformation trees and stat scaling.
  - `world.py` – map layout and room metadata.

Tests like `tests/test_combat.py`, `tests/test_skills.py`, `tests/test_progression.py`, and `tests/test_world_features.py` map directly to these modules and provide good examples of expected behaviour.

### app/main.py – FastAPI and WebSocket wiring

`app/main.py` is the primary composition root:

- Creates a `FastAPI` app using `settings.PROJECT_NAME` and configures logging.
- Sets up `slowapi` rate limiting and its exception handler.
- Adds CORS middleware with `settings.CORS_ORIGINS`.
- Includes the versioned API router from `app.api.api` under `settings.API_V1_STR`.
- Mounts `static/` at `/static` and configures Jinja2 templates from `templates/`.
- Defines HTML routes for:
  - `/` – landing or entry page.
  - `/create-character` – character creation UI.
  - `/game` – main game client page.
- Creates a `ConnectionManager` and a `GameEngine(manager)` instance.
- Exposes a WebSocket endpoint at `/ws` which:
  - Requires a `token` query parameter; uses `get_user_from_token` to resolve the current user.
  - Looks up the corresponding `Player` using `SessionLocal`.
  - On success, registers the WebSocket with `ConnectionManager`, calls `engine.refresh_ui(player)`, then enters a receive loop.
  - For each incoming command:
    - Enforces `MAX_COMMAND_LENGTH`; if exceeded, sends a system message and ignores the command.
    - Otherwise delegates to `engine.process_command(player.id, data, db)`.
  - Handles disconnects and errors with logging and appropriate WebSocket close codes.

Changes to any of the following have cross-cutting impact and should be approached carefully:

- WebSocket auth/token handling and `ConnectionManager` APIs.
- `GameEngine.process_command` verb routing and command semantics.
- Core constants and messages in `app/core/constants.py` and `app/core/messages.py`.
- SQLAlchemy models and Alembic migrations.

### Tests

The `tests/README.md` documents the test suite layout. High-level mapping:

- `tests/test_auth.py` – signup/login, character creation, initial flux.
- `tests/test_races.py` – four races and their passives.
- `tests/test_skills.py` – skills, cooldowns, and flux display.
- `tests/test_flux_comprehensive.py` – complete flux lifecycle and INT scaling.
- `tests/test_combat.py` – combat mechanics and passive effects.
- `tests/test_progression.py` – leveling, stat growth, transformations.
- `tests/test_world_features.py` – movement, inventory, items, quests, NPCs, shops.

When making non-trivial gameplay or model changes, update or extend these tests instead of writing entirely new top-level suites.
