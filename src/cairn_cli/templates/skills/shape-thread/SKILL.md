---
name: "shape-thread"
description: "Take a Thread out of Exploring: confirm the entry gate, draft a problem-and-impact brief, and get the PM's proceed/hold/drop decision — moving the Thread to Framing, or setting its status to Parked or Rejected."
argument-hint: "thread id or path to the signal file(s) to shape"
metadata:
  product: cairn
  source: "specs/001-thread-fidelity-stages/spec.md (Exploring stage)"
user-invocable: true
disable-model-invocation: false
---

## What this does

Step 1 of Cairn's core flow (shape → assess → draft-spec → check-spec). Takes a Thread from `stage: Exploring` to `stage: Framing` (or sets `status: Parked`/`Rejected`), by confirming the Exploring exit gate is met, drafting a short problem-and-impact brief, and asking the PM to decide: proceed, hold, or drop.

You are acting on the PM's Thread. You draft and check gates; the PM decides.

## Required inputs

Before drafting, locate and read:
1. `charter.yaml` — modality, UI presence, profile (`solo`/`team`), org rules.
2. Every signal file referenced in the Thread's `inbound_refs` (committed, redacted versions only — never `signals/*/raw/`).
3. The Thread file. If it doesn't exist yet, create it with minimal frontmatter (`thread_id`, `stage: Exploring`, `status: Active`, `owner`, `inbound_refs`, `touches`), the same as `fast-track` does.
4. `architecture/<system>/overview.md` for every system in `touches`, to check existence (not full content yet — that's `assess-thread`/`draft-spec`'s job).

If any of these are missing and the user hasn't pointed you at them, ask for the paths rather than guessing.

Before drafting, run `cairn find "<a few key words from the signal>"` (a single cheap call, returning ids, stages and one-line snippets) to check for earlier Threads on the same ask. If an earlier Thread was `Rejected` or `Parked`, tell the PM what reason was recorded so the idea isn't argued again from scratch. If one is already in flight, ask whether to link to it instead of starting a new one. Open a matched file only if a snippet isn't enough. To list everything tied to one id, use `cairn find <id>`.

## Rules

1. **Check the Exploring exit gate before drafting.** Feedback signals need a recurring-theme threshold met (`themes`); requirement/mandate/idea signals need a named sponsor who validated it (`validated_by`); analytics signals need a `comparison` (a baseline, prior period, target or control) and a known `sample_size`, since a lone number can't show that anything changed or matters. If the gate isn't met, say exactly what's missing and ask the PM how they want to proceed — gates are guardrails, not a prison, so the PM can override, but never silently.
2. Draft a short problem-and-impact brief, grounded only in the signal(s) and any existing overview content. Never invent data. It answers whether this is worth solving, not just whether it's understood. A sponsor or a theme count opens the gate, but neither one shows the work is valuable. Cover each of these headings, and write "unknown" where the signals don't say:
   - **Problem:** what's broken and who's affected.
   - **Evidence:** what the signals actually show: how many, from whom, how recent, and how direct (a firsthand report, a secondhand summary, or a request for a specific solution). Rate it `strong`, `moderate`, or `thin`, and say why in one line. For analytics, weigh sample size, how big the gap to the comparison is, and how recent `pulled_on` is. A number shows what happens, not why: if no feedback signal explains it, say the cause is unknown and suggest pairing it with one.
   - **Alternatives:** what else could address the problem, including doing nothing and any workaround people already use.
   - **Why now:** what makes this timely, or "nothing specific" if that's the honest answer.
   - **Expected outcome:** the observable change if this works, and how we'd know (a metric or behavior). When an analytics signal is attached, state the outcome against its number and cite it (e.g. "drop-off at step 3 falls from 40%", from `analytics:ANLY-001`); the target itself still comes from the PM. If nobody can say, record that as an open question; don't invent a target.
3. Give a short case for and against proceeding (not a full jury debate — that's `assess-thread`/`jury-duty`'s job, not this skill's). Thin evidence or an unknown outcome goes in the case against. These don't block, but the PM should see them before deciding.
4. Ask the PM to decide: **proceed**, **hold**, or **drop**. Never decide this yourself.
5. **On proceed:** check every system in `touches` has an overview file with a named owner (mirrors `check-spec`'s C17). Missing coverage is an Error on the `team` profile, a Warn on `solo`. Record the decision, set `stage: Framing`, and tell the PM this Thread is ready for `assess-thread` — Framing is when they bring others in.
6. **On hold:** set `status: Parked` (stage stays Exploring), record `reason` and `pickup_when`, the same fields `park-or-reject` writes.
7. **On drop:** set `status: Rejected` (stage stays Exploring), record `reason` and `reject_category`. This is searchable later so a dropped idea isn't re-argued from scratch.
8. Mark everything you write as agent-drafted.

## Org rules

If `charter.yaml` lists `org_rules` matching this Thread (restricted data, compliance/InfoSec mandate, public API contract change), remind the PM once ("this one usually needs a sign-off, want me to draft the ask?") and continue — unless that rule sets `enforcement: block`, in which case stop and say why.

## Output

Update the Thread file's frontmatter:

```yaml
stage: Framing       # proceed; on hold/drop stage stays Exploring
status: Active       # or Parked / Rejected
signal_refs: [...]
signal_types: [...]
validated_by: <name>       # requirement | mandate | idea signals
themes: [...]              # feedback signals only
touches: [...]
overview_coverage: ok | "warn: <systems missing an overview>"
evidence_strength: strong | moderate | thin
expected_outcome: "..."    # or "unknown"
shape_decision: proceed | hold | drop
reason: "..."              # hold or drop
pickup_when: "..."         # hold only
```

Plus the problem-and-impact brief as body text under the headings in rule 2, labeled agent-drafted.

If drafting surfaces a real action the PM needs to take outside the tool (e.g. "meet with the Architect to validate touches," "get UX to weigh in during Framing"), propose it as a line in the Thread's `## Open items` section (create the section if it doesn't exist yet) rather than mentioning it only in chat. Checking items off is the PM's job, not yours — see `whats-next`'s Checklists section for how this surfaces later.

## What you must not do

- Do not run the jury critique — hand off to `assess-thread` (which defaults to `jury-duty`).
- Do not draft the Spec.
- Do not set `status: Specified` — that only happens after a passing `check-spec` report, applied by the PM.
- Do not decide proceed/hold/drop yourself, and do not fabricate a sponsor validation or a theme threshold to force the gate open.
