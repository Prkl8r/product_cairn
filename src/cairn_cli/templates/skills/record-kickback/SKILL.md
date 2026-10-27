---
name: "record-kickback"
description: "Record why engineering sent a compiled Spec back: the reason and category, setting the Thread's status from Handed off back to Active so the Spec can be revised."
argument-hint: "thread id (or spec id) that was kicked back, plus the reason"
metadata:
  product: cairn
  source: "docs/spec-as-code-revision.md Part 1 section 4 (Thread Lifecycle, kickback categories)"
user-invocable: true
disable-model-invocation: false
---

## What this does

Records a fact: engineering (or the PM) sent a compiled Spec back for rework. Reopens the Spec that came back and logs why. On a Thread with several Specs, only that Spec goes back to `spec_status: drafted`; the others keep theirs. The Thread's `status` returns to `Active` (its stage stays `Validating`) if it was Specified or Handed off, and stays Active if it already was, so `revise-spec` has a reason to work from and the kickback-rate metric (segmented by track, per the docs) stays accurate.

## Required inputs

1. The Thread file, and which Spec came back (ask if the Thread has more than one). That Spec should be `spec_status: handed_off`, or the Thread `status: Handed off` for a single-Spec Thread.
2. The kickback reason, in the PM's own words, and which category it falls into: **missing edge case**, **ambiguous criterion**, **wrong constraint**, or **scope change**. Ask if the PM doesn't specify one.

## Rules

1. Never infer the category from the reason text — ask if it's ambiguous. These categories feed a metric; guessing wrong quietly corrupts it.
2. This skill only records the fact. It does not redraft anything — hand off to `revise-spec` once this is recorded.
3. If the PM wants to revise a Spec without a formal eng kickback (their own second thoughts, a new signal arrived), record that as the reason and skip the category — categories are for the metric, not required for a PM-initiated revision.

## Output

Update the Thread file:

```yaml
status: Active             # stage stays Validating
kickbacks:                 # one entry per kickback, newest last
  - spec_id: SPEC-NNN
    reason: "..."
    category: missing_edge_case | ambiguous_criterion | wrong_constraint | scope_change | null
    date: <date>
```

and set `spec_status: drafted` in that Spec's frontmatter (the only change this skill makes to a Spec). An older Thread with flat `kickback_reason`/`kickback_category`/`kickback_date` keys: move them into the first `kickbacks` entry.

## What you must not do

- Do not touch the Spec beyond setting `spec_status: drafted`; redrafting is `revise-spec`'s job.
- Do not set `status: Specified` or `Handed off` back — Specified follows a fresh passing `check-spec`, and Handed off follows a new handoff.
