---
name: "record-kickback"
description: "Record why engineering sent a compiled Spec back: the reason and category, setting the Thread's status from Specified back to Active so the Spec can be revised."
argument-hint: "thread id (or spec id) that was kicked back, plus the reason"
metadata:
  product: cairn
  source: "docs/spec-as-code-revision.md Part 1 section 4 (Thread Lifecycle, kickback categories)"
user-invocable: true
disable-model-invocation: false
---

## What this does

Records a fact: engineering (or the PM) sent a compiled Spec back for rework. Sets the Thread's `status` from `Specified` back to `Active` (its stage stays `Validating`) and logs why, so `revise-spec` has a reason to work from and the kickback-rate metric (segmented by track, per the docs) stays accurate.

## Required inputs

1. The Thread file — should be `status: Specified`.
2. The kickback reason, in the PM's own words, and which category it falls into: **missing edge case**, **ambiguous criterion**, **wrong constraint**, or **scope change**. Ask if the PM doesn't specify one.

## Rules

1. Never infer the category from the reason text — ask if it's ambiguous. These categories feed a metric; guessing wrong quietly corrupts it.
2. This skill only records the fact. It does not redraft anything — hand off to `revise-spec` once this is recorded.
3. If the PM wants to revise a Spec without a formal eng kickback (their own second thoughts, a new signal arrived), record that as the reason and skip the category — categories are for the metric, not required for a PM-initiated revision.

## Output

Update the Thread file:

```yaml
status: Active             # stage stays Validating
kickback_reason: "..."
kickback_category: missing_edge_case | ambiguous_criterion | wrong_constraint | scope_change | null
kickback_date: <date>
```

## What you must not do

- Do not touch the Spec file itself — that's `revise-spec`'s job.
- Do not set `status: Specified` back — that only happens after a fresh passing `compile-check` report.
