# Cairn — Todo Archive

Resolved follow-up items for the Cairn product repo.

## Done

- [x] 2026-10-17 **Provenance levels on traces** — Done: each trace carries a `basis` (direct, interpreted, inferred, decided) with its required field; new check C23; assess-thread edge cases get ids for inferred traces to point at
- [x] 2026-10-17 **Stronger Exploring gate** — Done: the shape-thread brief now covers evidence (with a strength rating), alternatives, why now and expected outcome; fast-track's light brief uses the same headings
- [x] 2026-10-15 **Deduplicate skill copies** — Done: `src/cairn_cli/templates/skills/` is now the only committed copy; `.claude/skills/` is git-ignored and installed with `cairn init --here --force --skills-only`
- [x] 2026-10-16 **Placeholder skills in whats-next** — Done: whats-next now says the four roadmap skills aren't built instead of routing to them
