---
name: "shape-thread"
description: "Move a Thread from Signal into Shape: confirm the entry gate, draft a problem-and-impact brief, and get the PM's proceed/hold/drop decision — carrying the Thread into Feasibility, Parked, or Rejected."
argument-hint: "thread id or path to the signal file(s) to shape"
metadata:
  product: cairn
  source: "docs/spec-as-code-revision.md Part 1 section 4 (Thread Lifecycle, Shape decision)"
user-invocable: true
disable-model-invocation: false
---

## What this does

Step 1 of Cairn's core flow (shape → assess → spec-generator → compile-check). Takes a Thread from `Signal` to `Feasibility` (or stops it at `Parked`/`Rejected`), by confirming the Signal→Shape entry gate is met, drafting a short problem-and-impact brief, and asking the PM to decide: proceed, hold, or drop.

You are acting on the PM's Thread. You draft and check gates; the PM decides.

## Required inputs

Before drafting, locate and read:
1. `charter.yaml` — modality, UI presence, profile (`solo`/`team`), org rules.
2. Every signal file referenced in the Thread's `inbound_refs` (committed, redacted versions only — never `signals/*/raw/`).
3. The Thread file. If it doesn't exist yet, create it with minimal frontmatter (`thread_id`, `state: Signal`, `owner`, `inbound_refs`, `touches`), the same as `fast-track` does.
4. `architecture/<system>/overview.md` for every system in `touches`, to check existence (not full content yet — that's `assess-thread`/`spec-generator`'s job).

If any of these are missing and the user hasn't pointed you at them, ask for the paths rather than guessing.

## Rules

1. **Check the Signal→Shape entry gate before drafting.** Feedback signals need a recurring-theme threshold met (`themes`); requirement/mandate/idea signals need a named sponsor who validated it (`validated_by`). If the gate isn't met, say exactly what's missing and ask the PM how they want to proceed — gates are guardrails, not a prison, so the PM can override, but never silently.
2. Draft a short problem-and-impact brief: what's broken, who's affected, why now — grounded only in the signal(s) and any existing overview content. Never invent data.
3. Give a short case for and against proceeding (not a full jury debate — that's `assess-thread`/`jury-duty`'s job, not this skill's).
4. Ask the PM to decide: **proceed**, **hold**, or **drop**. Never decide this yourself.
5. **On proceed:** check every system in `touches` has an overview file with a named owner (mirrors `compile-check`'s C17). Missing coverage is an Error on the `team` profile, a Warn on `solo`. Record the decision, set `state: Feasibility`, and tell the PM this Thread is ready for `assess-thread`.
6. **On hold:** set `state: Parked`, record `reason` and a `revisit_date`.
7. **On drop:** set `state: Rejected`, record `reason`. This is searchable later so a dropped idea isn't re-argued from scratch.
8. Mark everything you write as agent-drafted.

## Org rules

If `charter.yaml` lists `org_rules` matching this Thread (restricted data, compliance/InfoSec mandate, public API contract change), remind the PM once ("this one usually needs a sign-off, want me to draft the ask?") and continue — unless that rule sets `enforcement: block`, in which case stop and say why.

## Output

Update the Thread file's frontmatter:

```yaml
state: Feasibility   # or Parked / Rejected
signal_refs: [...]
signal_types: [...]
validated_by: <name>       # requirement | mandate | idea signals
themes: [...]              # feedback signals only
touches: [...]
overview_coverage: ok | "warn: <systems missing an overview>"
shape_decision: proceed | hold | drop
reason: "..."              # hold or drop
revisit_date: <date>       # hold only
```

Plus the problem-and-impact brief as body text, labeled agent-drafted.

## What you must not do

- Do not run the jury critique — hand off to `assess-thread` (which defaults to `jury-duty`).
- Do not draft the Spec.
- Do not set `state: Contract` — that only happens via a passing `compile-check` report, applied by the PM/tracker.
- Do not decide proceed/hold/drop yourself, and do not fabricate a sponsor validation or a theme threshold to force the gate open.
