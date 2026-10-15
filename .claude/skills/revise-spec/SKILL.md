---
name: "revise-spec"
description: "Redraft a Spec that was kicked back, in place — same spec_id, a bumped revision number, and a short note on what changed and why — so engineering sees an update, not a new document."
argument-hint: "spec id to revise"
metadata:
  product: cairn
  source: "docs/spec-as-code-revision.md Part 1 section 4 (Contract to Feasibility kickback) and Part 2 (Spec Frontmatter Contract)"
user-invocable: true
disable-model-invocation: false
---

## What this does

`spec-generator` in "update, not create" mode. Takes a Spec that was kicked back (via `record-kickback`) or that the PM otherwise wants to revise, and redrafts only the affected slices and criteria — carrying everything else forward unchanged. The output is the same `spec_id` at a new `revision`, so what goes back to engineering reads as *SPEC-042, revision 2*, not a fresh document.

## Required inputs

1. The existing Spec file in full.
2. The parent Thread — should show `kickback_reason` and `kickback_category` (from `record-kickback`), or the PM's own reason for revising.
3. Any new signal or overview content relevant to the fix.

## Rules (do not deviate)

1. **Never allocate a new `spec_id`.** This is the one invariant that keeps a kicked-back Spec reading as an update. If you don't have the original `spec_id` to hand, stop and ask for it rather than guessing.
2. Identify exactly which slices/criteria the kickback reason touches. Redraft only those. Everything else — slices, criteria, traces, open questions — carries forward untouched.
3. Bump `revision` (starts at 1 on first draft, so a first revision is `revision: 2`).
4. Write a short "what changed and why" note, tied directly to the `kickback_reason`/`kickback_category` — this is what a reviewer reads first.
5. Same drafting rules as `spec-generator`: every criterion traces to a real source, no invented values, binary-or-threshold typing, agent-drafted labeling.
6. If the kickback reveals an edge case the original jury verdict missed, add it to the Thread's edge-case list (retroactively) so the record stays honest about what was missed and why.

## Output

Same Spec file, same `spec_id`, updated frontmatter:

```yaml
spec_id: SPEC-042          # unchanged
revision: 2
revised_from_kickback: "<kickback_reason, or the PM's stated reason>"
changelog:
  - revision: 2
    date: <date>
    reason: "..."
    changed_slices: [S2]
    changed_criteria: [AC-004]
# everything else (sections, slices, criteria, open_questions) carries forward,
# only the touched entries are redrafted
```

## What you must not do

- Do not create a new `spec_id` or a new file — same Spec, new revision.
- Do not touch slices/criteria the kickback reason doesn't mention.
- Do not mark it compiled — send it back through `compile-check` before it goes to engineering again.
- Do not set `state: Contract` yourself — that's `compile-check`'s pass, applied by the PM/tracker.
