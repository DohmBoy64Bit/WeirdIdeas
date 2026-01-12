# Pixolve Release Notes — v0.1.0 (2026-01-12)

Release date: 2026-01-12

Summary
-------
This release contains the initial development release (v0.1.0) with focus on stabilizing the backend game flow, improving test reliability, and preparing the codebase for Pydantic v2 migration.

Highlights
----------
- Migrated Pydantic model serialization from `.dict` to `.model_dump()` across the codebase.
- Replaced naive `datetime.utcnow()` usage with timezone-aware `datetime.now(timezone.utc)` and standardized chat timestamps to timezone-aware ISO format.
- Stabilized WebSocket integration tests (use blocking receives, context-managed WebSocket sessions) and added tests for chat timestamps and Pydantic migration detection.
- Added a CI workflow (`.github/workflows/ci.yml`) that runs tests and treats DeprecationWarnings as errors to catch regressions early.
- Replaced ad-hoc prints with structured `logger.debug` statements to make logs more test- and CI-friendly.

Developer & Upgrade Notes
-------------------------
- Pydantic: If your code previously used `.dict` on schema objects, switch to `.model_dump()` and verify any downstream serialization behavior (key names remain unchanged in current schemas).
- Datetimes: Token expiry and chat timestamps are now timezone-aware (UTC). If you persisted naive datetimes elsewhere, make them timezone-aware to avoid inconsistencies.
- Tests: CI runs `pytest -W error` (or `PYTHONWARNINGS=error pytest`) so deprecation warnings will fail the build. Run tests locally with `pytest -W error` while preparing changes that may emit deprecation warnings.

Breaking changes
----------------
- No user-facing API changes in this release. Internal serialization (Pydantic use) changed; downstream code relying on `.dict` in third-party consumer scripts should be updated to `.model_dump()`.

How to run tests locally
------------------------
- Install dependencies (or use the project `requirements.txt` if present)
- Run: `pytest -q` (CI enforces `pytest -W error`)

Where to find more
------------------
- Changelog: `CHANGELOG.md`
- Design & concepts: `Pixolve_Game_Concept_Document.md`

Reporting issues
----------------
Open GitHub Issues for bugs or feature requests (include reproduction steps and logs where available).

Thanks to everyone who contributed to this release!
