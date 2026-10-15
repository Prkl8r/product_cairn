# Cairn — Todo

Open follow-up items for the Cairn product repo.

## Open

- [ ] **Deduplicate `onboard-product` skill copies** — `.claude/skills/onboard-product/SKILL.md` and `src/cairn_cli/templates/skills/onboard-product/SKILL.md` are kept in sync by hand. Add a sync script (e.g. `scripts/sync_skill_templates.py`) that copies from `.claude/skills/` (source of truth) into `src/cairn_cli/templates/skills/`, plus a CI/pre-commit check that fails if they drift. Symlinks were considered and rejected: Windows checkouts need Developer Mode/admin and `core.symlinks=true`, and setuptools doesn't reliably follow symlinks into sdists/wheels.
