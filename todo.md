# Cairn — Todo

Open follow-up items for the Cairn product repo.

## Open

- [ ] **Deterministic compile-check** — build `cairn compile <spec-id>` so the C01–C26 rules run as code instead of by hand
  Running all 22 checks by hand was the heaviest step in the first fast-track run. `cairn handoff` already trusts the compile report's verdict, so the gate should come from code.
  The 2026-10-27 Haiku test run confirmed it: `cairn check` later found 14 errors in two Specs the agent had passed.
  Mechanical half shipped as `cairn check` (C01, C02, C04–C10, C20, C21, C23, C27, C28); handoff now refuses on its Errors. Still by hand: C03, C11–C19, C22, C24–C26.
- [ ] **Cross-repo library refs** — define how a `trace.ref` points at a library file in another repo (C05 currently warns)
- [ ] **Front end for non-technical PMs** — P2: a web or IDE front end that hides the `cairn` commands, YAML and git behind forms and a Thread board
  Wider adoption needs it, but it's a separate product. Decide first who the audience is; the plugin only removes the install step.
- [ ] **Track-comparison metrics** — P2: report kickback rate by track (fast vs normal) and assumption burn-down by stage
  Needs real Threads first. Later, use the numbers to suggest when fast track shouldn't be used (e.g. API changes).
- [ ] **Overview freshness indicator** — P2: show how recently each overview was verified (from `last_verified` and `review_ttl`) in `ledger` or `doctor`
  A stale overview that passes every check gives false confidence. Could also feed fast-track caution flags.
- [ ] **Jury vs single-critique test** — P2: run one Thread through both a single critique and the Advocate/Skeptic/Judge jury, and compare what each finds
  A cheap stand-in for a full eval harness. If the jury adds nothing, simplify it.
- [ ] **Experiment as Thread output** — P3: note in the master doc that a Thread could produce a hypothesis-and-test artifact instead of a Spec
  A known gap, not a build item yet.
- [ ] **Change impact drives enablement** — P3: derive enablement work from what a change affects (support, sales, docs, training) instead of a checklist on the Spec
- [ ] **hand-off skill path untested** — rerun the test through the `hand-off` skill with no target configured, so the "how does your team work" setup flow gets exercised
  The Haiku agent bypassed it with `cairn handoff --to export`; make the skill harder to skip or have whats-next point at it.
- [ ] **Overview L1 → L2 promotion** — add a skill or command to name an owner and mark an overview verified
  Jury and check-spec both warned about all-L1 overviews, but there's no step to fix it.
- [ ] **Recurring-theme gate support** — count/link signals sharing a theme so the feedback exit gate isn't judged by eye
- [ ] **Commercial context for monetisation work** — give the charter or Thread a place for pricing, tiers and store billing constraints (App Store / Play)
  The premium mandate had no home for these; the jury found payment/sync edge cases with nothing to trace them to.
- [ ] **Separate PM in test runs** — rerun the end-to-end test with a human or a separate agent as PM, so Review Brief acknowledgement and PM decisions are real
- [ ] **Thread priority, user-configured** — add an optional `priority` on Threads, scored by a scheme the user picks in `.cairn/config.yaml`; `ledger`, `whats-next` and `snapshot` sort by it
  Keep it light: a sorting aid for busy weeks, not a Jira-style backlog tool. Default scheme: High/Medium/Low.
  Built-in schemes: High/Medium/Low, levels (P0–P3), MoSCoW (Must/Should/Could/Won't), RICE (Reach × Impact × Confidence ÷ Effort) and ICE (Impact × Confidence × Ease).
  Custom: the config can define its own ordered levels, or named score fields plus a formula. `shape-thread` asks for it at the proceed decision; `doctor` warns when a value doesn't fit the configured scheme.
  Found in the Haiku test run: with 7 signals and 4 Threads, nothing said what to work on next.
- [ ] **Thread size, user-configured** — add an optional `size` on Threads (or per planned Spec), with the scheme picked in `.cairn/config.yaml`; `ledger` and `snapshot` show it next to priority
  Same light touch as priority: a rough signal for busy weeks, not estimation tooling. Default scheme: Small/Medium/Large.
  Built-in schemes: Small/Medium/Large, T-shirt (XS–XL), story points (Fibonacci 1–13) and ideal days. Custom: the config lists its own ordered values.
  When the priority scheme is RICE, its Effort can default from size instead of being asked twice. `shape-thread` asks for a first guess; `draft-spec` lets the PM revise it once slices exist.
