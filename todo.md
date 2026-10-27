# Cairn — Todo

Open follow-up items for the Cairn product repo.

## Open

- [ ] **Deterministic compile-check** — build `cairn compile <spec-id>` so the C01–C26 rules run as code instead of by hand
  Running all 22 checks by hand was the heaviest step in the first fast-track run. `cairn handoff` already trusts the compile report's verdict, so the gate should come from code.
- [ ] **Deferred questions vs. starting work** — decide whether deferred open questions block starting implementation or only finishing a slice
  An engineer reading a Spec cold couldn't tell if `brief_ack` plus outstanding deferrals meant "go". Write the rule into the Spec template and check-spec.
- [ ] **Either/or criterion wording** — add a C08-style lint against "either/or" phrasing ("within or in place of") in criterion text
- [ ] **Lineage line** — render Signal → Thread → Spec ids in the Thread and Spec templates so the hierarchy reads without the design doc
- [ ] **Self-sourced signal type** — decide whether internal notes and dev-noticed items need their own signal type or clearer guidance under `idea`
- [ ] **Overview depth on fast track** — add a time-box or a "stop when you can answer these questions" rule for stub L1 overviews
- [ ] **Cross-repo library refs** — define how a `trace.ref` points at a library file in another repo (C05 currently warns)
- [ ] **Default review_ttl** — decide whether stub overviews get a default `review_ttl` so C16 has something to check
- [ ] **Deferred-risk follow-up** — let a deferred risk (e.g. accessibility) carry `needs_decision` and a re-surface point so it doesn't get forgotten
- [ ] **CLI test coverage** — add tests for `ledger`, `find`, `snapshot`, `init` and `doctor`
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
