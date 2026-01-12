# Pixolve Project Checklist

This file tracks high-level tasks, their statuses, and short notes.

- [x] Implement MVP backend (FastAPI, WebSockets, services)
- [x] Implement frontend skeleton (React components, WebSocket client)
- [x] Add WebSocket ConnectionManager and message shapes (lobby_update, chat, game_started, start_round, reveal_step, guess_result, scoreboard_update, game_finished)
- [x] Implement game service, scoring, and XP awarding
- [x] Add unit & integration tests for services and WebSocket flows
- [x] Fix test flakiness (use blocking receives, context-managed websockets)
- [x] Replace `print` debugging with `logger.debug`
- [x] Replace deprecated `dict()` with `model_dump()` for Pydantic models
- [x] Make datetime handling timezone-aware (`datetime.now(timezone.utc)`) ✅
- [x] Add chat timestamp timezone-aware test ✅

Remaining / follow-up items:
- [ ] Improve logging format and enable test-time debug config

Notes
- All tests currently pass locally (17 passed, no DeprecationWarnings under stricter CI settings).
- CI workflow added to run tests and fail on deprecation warnings (`.github/workflows/ci.yml`).