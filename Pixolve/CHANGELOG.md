# Changelog

All notable changes to this project are documented in this file.

## [2026-01-12] - v0.1.0 (released)
- Migrated Pydantic `.dict` usage to `.model_dump()` to align with Pydantic v2.
- Replaced naive `datetime.utcnow()` calls with timezone-aware `datetime.now(timezone.utc)`.
- Added WebSocket tests for chat timestamps (timezone-aware ISO format).
- Fixed flaky WebSocket tests by using blocking reads and context-managed connections.
- Replaced temporary print-based debugging with `logger.debug` and cleaned up logs.
- Added a Pydantic migration test (`tests/test_pydantic_migration.py`) that scans for legacy `.dict` usage.
- Added a CI workflow (`.github/workflows/ci.yml`) to run tests and treat deprecation warnings as errors.
- Updated documentation (`Pixolve_Game_Concept_Document.md`) and added a project `CHECKLIST.md`.


*Note: Versioning is informal for now; update semantic versioning and release notes when preparing a release.*