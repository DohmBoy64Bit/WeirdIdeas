# Alembic Database Migrations

## Overview
This project now uses Alembic for database schema migrations. This makes it easy to track and apply database changes.

## Common Commands

### Create a new migration
When you add/modify/remove a model field:
```bash
alembic revision --autogenerate -m "Description of change"
```

Example:
```bash
alembic revision --autogenerate -m "Add base_flux to Race model"
```

### Apply migrations
To update your database to the latest schema:
```bash
alembic upgrade head
```

### Rollback migrations
To undo the last migration:
```bash
alembic downgrade -1
```

### View migration history
```bash
alembic history
```

### Check current version
```bash
alembic current
```

## Workflow Example

1. **Modify a model** (e.g., add a field to Player):
   ```python
   # In app/models/player.py
   new_field = Column(String, default="value")
   ```

2. **Create migration**:
   ```bash
   alembic revision --autogenerate -m "Add new_field to Player"
   ```

3. **Review the migration** in `alembic/versions/xxxxx_add_new_field.py`

4. **Apply migration**:
   ```bash
   alembic upgrade head
   ```

## Migration Files

Migrations are stored in `alembic/versions/`. Each file contains:
- `upgrade()`: Changes to apply
- `downgrade()`: Changes to rollback

## Notes

- Always review auto-generated migrations before applying
- Commit migration files to version control
- Never edit migrations that have been applied to production
- For data migrations, you may need to write custom migration code

## Troubleshooting

**"Target database is not up to date"**
```bash
alembic stamp head
```

**"Can't locate revision"**
Delete `alembic/versions/*.py` and start fresh:
```bash
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```
