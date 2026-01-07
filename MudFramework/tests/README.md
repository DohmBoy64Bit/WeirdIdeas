# Pytest Test Suite

## Overview
Comprehensive pytest test suite covering all game features.

## Test Structure

```
tests/
├── conftest.py                 # Shared fixtures
├── test_auth.py               # Authentication & character creation
├── test_races.py              # All 4 races & passives
├── test_skills.py             # Skills & cooldowns
├── test_flux_comprehensive.py # Complete flux system
├── test_combat.py             # Combat mechanics
├── test_progression.py        # Leveling & transformations
└── test_world_features.py     # Movement, inventory, quests
```

## Running Tests

**All tests:**
```bash
python -m pytest tests/ -v
```

**Specific test file:**
```bash
python -m pytest tests/test_flux_comprehensive.py -v
```

**Specific test class:**
```bash
python -m pytest tests/test_races.py::TestAllRaces -v
```

**Specific test:**
```bash
python -m pytest tests/test_auth.py::TestAuthentication::test_signup -v
```

**With coverage:**
```bash
python -m pytest tests/ --cov=app --cov-report=html
```

## Test Coverage

### ✅ Authentication (test_auth.py)
- User signup
- User login
- Invalid credentials
- Character creation (all races)
- Flux initialization

### ✅ Races & Passives (test_races.py)
- Zenkai (80 base flux, Battle Hardened)
- Vitalis (120 base flux, Regeneration)
- Terran (100 base flux, Tactical Mind)
- Glacial (70 base flux, Ice Armor)
- Race-specific skills
- Passive ability descriptions

### ✅ Flux System (test_flux_comprehensive.py)
- Initialization at max
- Flux formula (base + INT*5)
- Skill consumption
- Insufficient flux blocking
- 10% per round regeneration
- Restore after combat
- Restore on level up
- INT scaling

### ✅ Skills (test_skills.py)
- Skills list command
- Skill info tooltips
- Flux cost display
- Cooldown mechanics
- Race requirements

### ✅ Combat (test_combat.py)
- Hunt command
- Attack mechanics
- Flee command
- Passive abilities in combat

### ✅ Progression (test_progression.py)
- Leveling up
- Stat increases
- Skill unlocking
- Transformations
- Revert command

### ✅ World Features (test_world_features.py)
- Movement (NSEW)
- Look command
- Inventory management
- Item usage
- Item stacking
- Quest system
- NPC interactions
- Shop/buying

## Fixtures

**Session-scoped:**
- `test_credentials` - Unique test account
- `auth_token` - Auth token for API calls
- `auth_headers` - Authorization headers
- `test_player` - Test character (Zenkai)

**Function-scoped:**
- `ws_connection` - WebSocket connection (auto-cleanup)

**Helper Functions:**
- `send_command(ws, cmd)` - Send command and collect responses

## Best Practices

1. **Isolation**: Each test is independent
2. **Cleanup**: Fixtures handle teardown
3. **Assertions**: Clear, specific assertions
4. **Coverage**: All features tested
5. **Organization**: Logical test grouping

## CI/CD Ready

The test suite is ready for continuous integration:
- No manual intervention required
- Automatic setup/teardown
- Clear pass/fail reporting
- Can run in parallel with pytest-xdist
