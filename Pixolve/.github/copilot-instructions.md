# Copilot Instructions for Pixolve

Short, actionable guidance for AI contributors working on Pixolve. Focus on immediate, discoverable patterns and files so you can be productive without extra context.

- Project layout
  - Backend: `backend/` (FastAPI). Key files: `backend/app/core.py` (create_app factory), `backend/app/main.py` (uvicorn entry). Expected subfolders: `api/`, `services/`, `models/`, `schemas/`, `sockets/`.
  - Frontend: `frontend/` (React). Entry points: `frontend/main.js` and `frontend/App.js`. Tailwind CSS is used per the game doc.
  - High-level game spec: `Pixolve_Game_Concept_Document.md` documents rules, scoring, and architecture—update this when making behavioral changes.

- How to run things (discoverable / canonical ways)
  - Backend: run the module (it calls uvicorn in the `__main__` guard): `python backend/app/main.py` (or use uvicorn: `uvicorn backend.app.main:app --reload`).
  - Frontend: standard React tooling is expected in `frontend/` (look for `package.json`); typical commands: `npm start` / `npm run build` if present.
  - CI: a basic GitHub Actions workflow is added at `.github/workflows/ci.yml` that runs Python tests (`pytest`). Add frontend CI steps if a `package.json` is added.

- Code organization & conventions (follow the game doc)
  - Use the service-layer pattern: keep business logic in `backend/app/services/`; API routes should only validate and map requests/responses.
  - Models are data containers only; sockets live in `backend/app/sockets/` and use WebSockets for real-time events.
  - Follow PEP8/PEP257, keep files ~<=300 lines, and avoid magic numbers—centralize timers, scores, and curves in a config module.
  - Frontend structure: prefer `components/`, `pages/`, `services/`, `styles/`, and `utils/` as indicated by the design doc.

- Testing & safety
  - Unit tests should target services and scoring logic; services must be importable and testable without running the HTTP server.
  - When changing scoring/timer logic, add tests that assert numeric behavior (e.g., point decay, min/max values) and reference constants in the config.
  - XP & leveling: XP is derived from points (XP = points // 10) and a simple level curve is used (level thresholds in `backend/app/config.py`). Add tests for XP awarding and level-up behavior when changing scoring or XP formulas.

- Common tasks & examples
  - Add an API route: place request/response schemas in `schemas/`, implement validation in an API router under `api/`, and call into `services/` for logic. Register the router via `create_app()` in `backend/app/core.py`.
  - Add a new category: add data (name, images, difficulty) under a categories resource (not business logic). Use `backend/app/services/category_service.py` and `backend/data/images/` for image assets; import images via the `import_images_from_dir` helper or the `POST /categories/{category_id}/upload` endpoint. Frontend hosts select a category when creating a lobby (see `frontend/components/Lobby.js`). The system is data-driven so categories can be updated without changing gameplay logic.
  - Debugging backend: run `python backend/app/main.py` and reproduce socket events using a websocket client or browser devtools.

- Realtime (WebSocket) events (quick reference) ✅
  - Connect: `GET /ws?token=<token>&lobby=<lobby_id>` — server validates token and lobby, then keeps the socket open.
  - Sent from client (examples):
    - `{"type":"join_lobby","data":{"player": {"id":"alice","username":"alice"}}}` — request a lobby state broadcast.
    - `{"type":"player_ready","data":{"player_id":"alice","ready":true}}` — toggle ready state.
    - `{"type":"chat","data":{"player":"alice","text":"Hi!"}}` — chat message (server attaches `ts`).
    - `{"type":"start_game","data":{"player":{"id":"host","username":"host"}}}` — host starts the game.
    - `{"type":"submit_guess","data":{"player_id":"p1","text":"my guess"}}` — submit a round guess.
  - Broadcasts from server (examples):
    - `{"type":"lobby_update","data":{"players":[...]}}` — current lobby players.
    - `{"type":"chat","data":{"player":"alice","text":"Hi!","ts":"2026-01-01T00:00:00"}}` — chat message with server timestamp.
    - `{"type":"game_started","data":{"game_id":"..."}}` — game started notification.
    - `{"type":"start_round","data":{...}}` / `{"type":"reveal_step","data":{"pixelation": 8}}` — game round events to coordinate UI reveals.
    - `{"type":"guess_result","data":{"player_id":"p1","text":"...","correct":true}}` — server-evaluated guess result.
    - `{"type":"scoreboard_update","data":{"scores":{"p1": 120}}}` — scoreboard update broadcast.

  Keep this section up-to-date when adding new realtime events — frontend and tests rely on these message shapes.

- What to avoid
  - Don't change gameplay rules without updating `Pixolve_Game_Concept_Document.md` and adding/adjusting tests that cover affected behavior.
  - Avoid putting business logic directly in API handlers or in React components—keep services and UI concerns separate.

If anything here is unclear or you want this document to cover additional workflows (CI, release, local dev setup), tell me which area to expand and I will iterate. Thanks!