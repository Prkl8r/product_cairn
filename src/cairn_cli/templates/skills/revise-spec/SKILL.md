---
name: "revise-spec"
description: "Redraft a Spec that was kicked back, in place — same spec_id, a bumped revision number, and a short note on what changed and why — so engineering sees an update, not a new document."
argument-hint: "spec id to revise"
metadata:
  product: cairn
  source: "specs/001-thread-fidelity-stages/spec.md (Kickback) and docs/spec-as-code-revision.md Part 2 (Spec Frontmatter Contract)"
user-invocable: true
disable-model-invocation: false
---

## What this does

`draft-spec` in "update, not create" mode. Takes a Spec that was kicked back (via `record-kickback`) or that the PM otherwise wants to revise, and redrafts only the affected slices and criteria — carrying everything else forward unchanged. The output is the same `spec_id` at a new `revision`, so what goes back to engineering reads as *SPEC-042, revision 2*, not a fresh document.

## Required inputs

1. The existing Spec file in full.
2. The parent Thread — should show `kickback_reason` and `kickback_category` (from `record-kickback`), or the PM's own reason for revising.
3. Any new signal or overview content relevant to the fix.

## Rules (do not deviate)

1. **Never allocate a new `spec_id`.** This is the one invariant that keeps a kicked-back Spec reading as an update. If you don't have the original `spec_id` to hand, stop and ask for it rather than guessing.
2. Identify exactly which slices/criteria the kickback reason touches. Redraft only those. Everything else — slices, criteria, traces, open questions — carries forward untouched.
3. Bump `revision` (starts at 1 on first draft, so a first revision is `revision: 2`).
4. Write a short "what changed and why" note, tied directly to this Spec's latest entry in the Thread's `kickbacks` (`reason`, `category`; older Threads use flat `kickback_reason`/`kickback_category`) — this is what a reviewer reads first.
5. Same drafting rules as `draft-spec`: every criterion traces to a real source with a `basis` on each trace (add one to carried-forward traces that lack it, without changing anything else), no invented values, binary-or-threshold typing, agent-drafted labeling.
6. **On a Thread with several Specs, revise only this one.** Read the sibling Specs so the revision doesn't duplicate or contradict them, but never edit them. If the fix belongs in a sibling, stop and say so. Update this Spec's Status in the `## Planned Specs` table to `drafted`.
7. If the kickback reveals an edge case the original jury verdict missed, add it to the Thread's edge-case list (retroactively) so the record stays honest about what was missed and why.

## Output

Same Spec file, same `spec_id`, updated frontmatter:

```yaml
spec_id: SPEC-042          # unchanged
revision: 2
revised_from_kickback: "<the kickback reason, or the PM's stated reason>"
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
- Do not mark it compiled — send it back through `check-spec` before it goes to engineering again.
- Do not set `status: Specified` or `spec_status: specified` yourself — that follows `check-spec`'s pass, applied by the PM. The revised Spec keeps `spec_status: drafted`.
