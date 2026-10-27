# Cairn — Todo Archive

Resolved follow-up items for the Cairn product repo.

## Done

- [x] 2026-10-27 **Default review_ttl** — Done: overviews.review_ttl in config (default 180d), used by C16 when an overview has none and written into stubs
- [x] 2026-10-27 **Overview depth on fast track** — Done: fast-track's stub overviews stop at four questions (purpose, boundaries, interfaces touched, constraints), the rest TBD
- [x] 2026-10-27 **Self-sourced signal type** — Done: new `internal` signal type (INT- ids) whose Exploring gate is the PM's written cost of not doing it; idea now means a championed proposal
- [x] 2026-10-27 **Deferred questions vs. starting work** — Won't do: Cairn's part ends at handoff; the receiving process decides what deferrals block
- [x] 2026-10-27 **Suggest bundle and journey at the right moment** — Done: shape-thread offers bundle-threads for Threads sharing signals/themes and map-journey for user-facing changes on proceed; assess-thread offers map-journey before the jury
- [x] 2026-10-27 **Record which jury seats ran** — Done: jury-duty returns `jury_seats` and the transcript, assess-thread saves them and refuses without a Judge, and `cairn check` C28 fails the Spec
- [x] 2026-10-27 **Enforce the scope check** — Done: scope_decision is always recorded (new `single` value); draft-spec refuses without it and `cairn check` C27 fails the Spec
- [x] 2026-10-27 **Lineage line** — Done: shape-thread, draft-spec and fast-track open Thread and Spec bodies with a `**Lineage:**` line
- [x] 2026-10-27 **Reviewer reminder at Validating** — Done: assess-thread, draft-spec and fast-track all emit the reminder in a fixed format, repeat it to the PM, and flag TBD owners
- [x] 2026-10-27 **Onboard missing Appendix E** — Done: the overview template is inlined in onboard's SKILL.md
- [x] 2026-10-27 **Surface untriaged signals** — Done: ledger JSON carries an `untriaged` list and whats-next lists each one with a nudge
- [x] 2026-10-27 **CLI test coverage** — Done: tests/test_cli.py covers init, doctor, ledger, find and snapshot
- [x] 2026-10-27 **Unknown frontmatter keys** — Done: `cairn doctor` warns on keys no skill writes, suggests the closest known key, and accepts `extra_keys` from config
- [x] 2026-10-27 **Either/or criterion wording** — Done: `cairn check` C08 now flags "either … or", "or in place of" and "and/or" in criterion text
- [x] 2026-10-27 **Broken refs block handoff** — Done: `cairn check` runs C05/C06 as code and `cairn handoff` refuses on any mechanical Error, whatever the compile report says; ledger now resolves path-form refs like `backend-api/overview.md`
- [x] 2026-10-27 **Validate ref syntax** — Won't do: false positive; the bare values in the test run were `touches`/`signal_types`, not refs
- [x] 2026-10-17 **Provenance levels on traces** — Done: each trace carries a `basis` (direct, interpreted, inferred, decided) with its required field; new check C23; assess-thread edge cases get ids for inferred traces to point at
- [x] 2026-10-17 **Stronger Exploring gate** — Done: the shape-thread brief now covers evidence (with a strength rating), alternatives, why now and expected outcome; fast-track's light brief uses the same headings
- [x] 2026-10-15 **Deduplicate skill copies** — Done: `src/cairn_cli/templates/skills/` is now the only committed copy; `.claude/skills/` is git-ignored and installed with `cairn init --here --force --skills-only`
- [x] 2026-10-16 **Placeholder skills in whats-next** — Done: whats-next now says the four roadmap skills aren't built instead of routing to them
