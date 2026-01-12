# Pixolve -- Game Concept Document

## 1. Game Overview

**Game Name:** Pixolve\
**Genre:** Multiplayer Guessing / Party Web Game\
**Platform:** Web App

### Tech Stack

-   **Backend:** Python, FastAPI\
-   **Frontend:** JavaScript, Tailwind CSS\
-   **Real-time:** WebSockets\
-   **Auth & Data:** Custom authentication (no email required)

### Core Idea

Players compete in real-time to guess what an image is while it
gradually becomes less pixelated. The faster a player guesses correctly,
the more points and XP they earn.

Pixolve is designed to be: - Fast-paced - Social - Easy to learn -
Highly expandable (categories, modes, rewards)

------------------------------------------------------------------------

## 2. Core Gameplay Loop

1.  Players join a lobby (5 or 10 players -- configurable).
2.  A game consists of **5 rounds**.
3.  Each round:
    -   A heavily pixelated image is shown.
    -   A countdown timer begins.
    -   The image progressively unpixelates.
    -   Players submit guesses via chat.
4.  Correct guess:
    -   Player is notified.
    -   Points awarded based on speed.
    -   Guess input locked for the round.
5.  Round ends when:
    -   Timer expires **OR**
    -   All players guess correctly.
6.  After all rounds:
    -   Scores are tallied.
    -   XP is awarded.
    -   Results screen is shown.

------------------------------------------------------------------------

## 3. Image Reveal System

-   Images start at maximum pixelation.
-   Pixelation decreases in timed steps.
-   Reveal speed is consistent per round.
-   Final seconds show the image clearly.

**Optional Enhancements** - Blur removal in addition to pixelation. -
Dynamic reveal curve (slow → fast).

------------------------------------------------------------------------

## 4. Categories System

Pixolve uses a modular category system.

**Examples** - Nature - Movies - Animals - Video Games - Landmarks -
Cartoons

Each category includes: - Name - Description - Image set - Difficulty
rating (optional) - Active/Inactive toggle

**Selection** - Host-selected or random - Mixed categories option

------------------------------------------------------------------------

## 5. Multiplayer & Lobby System

### Lobby Types

-   Public
-   Private (invite code)

### Lobby Settings

-   Max players
-   Category selection
-   Round count
-   Guess timer length

### Game Room Features

-   Game-only chat
-   Live scoreboard
-   Pixelation progress indicator
-   Player status list

------------------------------------------------------------------------

## 6. Chat System

### Global Chat

-   Light moderation
-   Optional slow mode

### Game Chat

-   Used for guesses
-   Correct guesses hidden
-   Incorrect guesses optionally visible

### Filters

-   **Username:** Extremely strict
-   **Chat:** Blocks slurs, hate speech, extreme profanity

------------------------------------------------------------------------

## 7. Scoring System

-   Max points per round: **1000**
-   Points decrease over time
-   Minimum points: **100**

**Bonuses** - First correct guess - Perfect game - Speed streaks

------------------------------------------------------------------------

## 8. XP & Leveling

**XP Sources** - Correct guesses - Match placement - Match completion -
Achievements

**Levels** - Infinite leveling - Increasing XP curve

**Titles** - Rookie (1--9) - Solver (10--19) - Pixel Hunter (20--29) -
Visionary (30--39) - Mind Reader (40--49) - Pixolve Elite (50+)

------------------------------------------------------------------------

## 9. User Accounts & Authentication

-   Username + password
-   No email required
-   One-time recovery code (hashed, shown once)

**Security** - Password hashing - Rate-limited logins - Recovery code
stored hashed

------------------------------------------------------------------------

## 10. User Profiles

Public profiles include: - Username - Level & XP - Rank - Games played -
Correct guess rate - Favorite category - Awards - Name cosmetics

------------------------------------------------------------------------

## 11. Global Leaderboards

**Types** - All-time points - Weekly XP - Total wins - Fastest average
guess

------------------------------------------------------------------------

## 12. Achievements System

Unlocks: - XP - Titles - Cosmetic effects

**Examples** - First Guess - 10 Wins - 100 Correct Guesses - Perfect
Match - Category Master

------------------------------------------------------------------------

## 13. UX & UI Philosophy

**Style** - Clean - Pixel-inspired - Modern + nostalgic

**Principles** - Minimal clicks - Clear feedback - Smooth transitions

------------------------------------------------------------------------

## 14. Backend Architecture (High-Level)

FastAPI handles: - Auth - Lobbies - Game state - Scoring & XP -
Leaderboards - WebSockets

------------------------------------------------------------------------

## 15. Future Expansions

-   Daily challenges
-   Ranked mode
-   Solo practice
-   Custom images (moderated)
-   Seasonal events
-   Spectator mode
-   Streamer delay mode

------------------------------------------------------------------------

## 16. Summary

Pixolve is a fast, social, competitive guessing game with strong
progression and modular design, ideal for both casual and competitive
players.

------------------------------------------------------------------------

## 17. Engineering Principles & Code Architecture Standards

### 17.1 Core Principles

-   **DRY**
-   **PEP 8 / 257 / 484**
-   **Separation of Concerns**
-   **Strict Modularity**
-   Max \~300 lines per file

### 17.2 Backend Folder Structure

    backend/
    ├── app/
    │   ├── main.py
    │   ├── core/
    │   ├── api/
    │   ├── services/
    │   ├── models/
    │   ├── schemas/
    │   ├── sockets/
    │   ├── filters/
    │   └── utils/

### 17.9 Engineering updates (2026-01-12)

- Migrated Pydantic usage to `.model_dump()` to align with Pydantic v2 and avoid deprecation warnings.
- Replaced naive UTC calls with timezone-aware datetimes (`datetime.now(timezone.utc)`).
- Added CI workflow (`.github/workflows/ci.yml`) that installs dependencies and runs `pytest -W error` (treat DeprecationWarnings as errors).
- Added automated tests to verify Pydantic migration (see `tests/test_pydantic_migration.py`) and a chat timestamp test that asserts a timezone-aware ISO timestamp is present on chat messages.
- Rationale: proactively prevent regressions and ensure a smooth v2 migration path.

### Changelog

A concise changelog is maintained in `CHANGELOG.md` (root). The 2026-01-12 entry summarizes the Pydantic migration, timezone-aware datetime changes, CI additions, test fixes, and logging cleanup.

For release preparation, add entries to `CHANGELOG.md` and bump the package version in the project metadata.
### 17.3 Responsibility Rules

-   API: validation & responses only
-   Services: all business logic
-   Models: data only
-   Sockets: real-time messaging

### 17.4 Frontend Structure

    frontend/
    ├── components/
    ├── pages/
    ├── services/
    ├── styles/
    └── utils/

### 17.5 Configuration

-   All timers, scores, XP curves centralized
-   No magic numbers

### 17.6 Testing

-   Unit test services
-   Test scoring, XP, filters
-   Services testable without API

### 17.7 Extensibility

-   Add categories without touching logic
-   Change scoring without UI changes
-   Add achievements without core edits

### 17.8 Final Philosophy

> Readable over clever\
> Explicit over implicit\
> Modular over monolithic
