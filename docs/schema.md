# VitaCompanion — Schema Reference

## Critical Column Names
- `users.full_name` (NOT `name`)
- `rag_documents`: NO `title` or `category` columns — use `doc_type` (text) for category, `metadata->>'title'` (jsonb) for title
- `Conversation` model: do NOT pass `created_at`/`updated_at` to constructor — set by DB default

## ENUMs — always use `create_type=False`
```python
Column(ENUM('val1', 'val2', name='type_name', create_type=False))
```

| Enum name       | Values |
|----------------|--------|
| `persona_style` | friend, coach, commander |
| `bot_type`      | orchestrator, nutrition, training, reporting, scheduler |
| `message_role`  | user, assistant, system |
| `report_period` | weekly, monthly, on_demand |
| `flag_type`     | none, physical, emotional, constraint_violation, rapid_weight_loss, pain_reported, hr_exceeded, overtraining_risk, medical_hold |
| `session_type`  | cardio, strength, mobility, rest, active_recovery |
| `intensity_level` | low, moderate, moderate_high, high |

## asyncpg Cast Syntax
Use `CAST(:param AS vector)` — never `:param::vector` (breaks asyncpg `$N` substitution).
Same for jsonb: `CAST(:param AS jsonb)`.

## Validation Rules (enforced in log_service.py)
- `weight_kg >= 0`
- `0 <= sleep_hours <= 24`
- `calories, protein_g, fat_g, carbs_g >= 0`
- `1 <= perceived_exertion <= 10`
- Chat message: non-empty, non-whitespace (422 before any DB call)
- Missing health_profile or persona_config: raises 404 before streaming starts

## Source of truth
`schema.sql` in project root. Run `psql vitacompanion < schema.sql` to recreate.
