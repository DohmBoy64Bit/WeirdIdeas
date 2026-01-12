# Pixolve API Specification (draft)

This file lists the canonical endpoints, WebSocket events, and example payloads to guide implementation.

## Auth
- POST /auth/login
  - Body: { "username": "alice" }
  - Response: { "token": "<jwt-or-similar>", "user": {"id":"u1","username":"alice"} }

## Lobby
- POST /lobbies
  - Body: { "max_players": 5, "category": "animals", "rounds": 5 }
  - Response: Lobby object
- POST /lobbies/{id}/join
  - Body: { "token": "..." }
  - Response: { "lobby": {...}, "players": [...] }
- POST /lobbies/{id}/leave

## Game
- POST /games/{lobby_id}/start
  - Starts a game for the lobby (host only)
- GET /games/{game_id}
  - Returns current `GameState`

## WebSocket (real-time)
Connect to: ws://host/ws?token=<token>&lobby=<lobby_id>

Messages are JSON with shape: { "type": "event_name", "data": {...} }

Important event types:
- join_lobby
- lobby_update (players, settings)
- start_round (round metadata)
- reveal_step (pixelation progress)
- submit_guess { player_id, text }
- guess_result { player_id, correct, points }
- end_round { scoreboard }
- game_over { final_scores }

Example `submit_guess`:
{ "type": "submit_guess", "data": { "player_id": "u1", "text": "cat" } }

## Schemas (references)
- User: id, username, display_name, level, xp
- Lobby: id, host_id, max_players, players[], category
- GameState: id, lobby_id, round_index, rounds[], players[], scoreboard
- RoundState: image_id, pixelation_level, timer_secs

---

Note: This is a living draft to be refined as services are implemented.