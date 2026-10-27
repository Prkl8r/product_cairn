# Cairn — Todo Archive

Resolved follow-up items for the Cairn product repo.

## Done

- [x] 2026-10-27 **Broken refs block handoff** — Done: `cairn check` runs C05/C06 as code and `cairn handoff` refuses on any mechanical Error, whatever the compile report says; ledger now resolves path-form refs like `backend-api/overview.md`
- [x] 2026-10-27 **Validate ref syntax** — Won't do: false positive; the bare values in the test run were `touches`/`signal_types`, not refs
- [x] 2026-10-17 **Provenance levels on traces** — Done: each trace carries a `basis` (direct, interpreted, inferred, decided) with its required field; new check C23; assess-thread edge cases get ids for inferred traces to point at
- [x] 2026-10-17 **Stronger Exploring gate** — Done: the shape-thread brief now covers evidence (with a strength rating), alternatives, why now and expected outcome; fast-track's light brief uses the same headings
- [x] 2026-10-15 **Deduplicate skill copies** — Done: `src/cairn_cli/templates/skills/` is now the only committed copy; `.claude/skills/` is git-ignored and installed with `cairn init --here --force --skills-only`
- [x] 2026-10-16 **Placeholder skills in whats-next** — Done: whats-next now says the four roadmap skills aren't built instead of routing to them
