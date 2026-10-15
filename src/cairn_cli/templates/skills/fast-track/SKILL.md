---
name: "fast-track"
description: "Take a Cairn Thread from Exploring straight to a drafted Spec: backfill Framing and Validating in light form, draft the Spec, and write a Review Brief for the PM to check."
argument-hint: "thread id or path to the signal file(s) to run through fast track"
metadata:
  product: cairn
  source: "docs/cairn-pilot-walkthrough.md step 5, docs/spec-as-code-revision.md Part 1 section 4 (Fast Track)"
user-invocable: true
disable-model-invocation: false
---

## What this does

Runs one Thread through Cairn's fast track: Exploring straight to a Spec draft, with the skipped stages (Framing, Validating) backfilled in lightweight form and a Review Brief the PM must read before acknowledging.

You are acting on the PM's Thread. You own none of it — you draft, the PM decides.

## Required inputs

Before drafting, locate and read:
1. `charter.yaml` — product modality, UI presence, profile (`solo`/`team`), write authority, org rules.
2. Every `architecture/<system>/overview.md` the work touches. If one doesn't exist, note it — do not invent its content.
3. The signal file(s) under `signals/<type>/<signal-id>.md` (the committed, redacted version — never the raw copy under `signals/*/raw/`).
4. The Thread file under `threads/<thread-id>.md`, if it exists. If it doesn't, create it with minimal frontmatter (`thread_id`, `stage: Exploring`, `status: Active`, `owner`, `inbound_refs`, `touches`) plus the one-paragraph description, before proceeding.

If any of these are missing and the user hasn't pointed you at them, ask for the paths rather than guessing.

## Rules (do not deviate)

1. Before drafting, ask up to 3 questions — only ones whose answers would change the Spec. If none are needed, say so and proceed.
2. Backfill the skipped stages in light form:
   - **Exploring → Framing:** a short problem-and-impact brief drafted from the signal.
   - **Framing:** a single-pass critique (not a full jury debate) listing the top edge cases and risks, each mapped to a criterion or deferred with a reason.
   - **Validating:** no supporting artifacts (mocks, API spec) are made and nobody has reviewed the draft yet. List the artifacts the normal track would have needed as skipped, and add a review reminder (sponsor, owners of systems in `touches`) to `## Open items`.

   Then set the Thread to `stage: Validating`, add `light_stages: [Framing, Validating]`, and add the Spec to its `outbound_refs`. Leave `status: Active`.
3. Every acceptance criterion is `binary` or carries a `threshold` (metric, operator, number, unit), and has at least one `trace` entry pointing to a real file. Quote the source where you can — never quote the raw/git-ignored copy.
4. Group criteria into ordered slices. Each slice gets a one-line `verify` note.
5. Never invent numbers, endpoints, field names, or limits. If a value has no source, ask the PM or list it as an open question — do not default it silently.
6. Describe observable behavior, not implementation (no frameworks, databases, internal structure).
7. Mark everything you write as agent-drafted.
8. Finish with a Review Brief (format below). If the work looks risky for a fast track (touches an unverified or missing overview, changes a public API, rests mostly on inferred assumptions), say so plainly as a caution flag — then proceed anyway. The call is the PM's, not yours.

## Org rules

If `charter.yaml` lists `org_rules` that match this Thread (restricted data, compliance/InfoSec mandate, public API contract change), remind the PM once ("this one usually needs a sign-off, want me to draft the ask?") and continue — unless that rule sets `enforcement: block`, in which case stop and say why.

## Output: the Spec

Write `specs/<spec-id>.md` using this frontmatter contract exactly (see `docs/spec-as-code-revision.md` Part 2 for the full schema):

```yaml
---
spec_id: SPEC-NNN
thread_id: THRD-NNN
charter_version: <from charter.yaml>
generated_by:
  skill: fast-track
  skill_version: 0.1.0
track: fast
skipped_gates: [Framing, Validating]
sections:
  problem: "..."
  out_of_scope: ["..."]
  error_states: ["..."]
  empty_states: ["..."]
  enablement_deps: ["..."]   # or "n/a: <reason>" when the profile is solo
slices:
  - id: S1
    name: "..."
    order: 1
    verify: "..."
open_questions: []            # each: text, status (answered | deferred | out_of_scope), reason, owner
criteria:
  - id: AC-001
    slice: S1
    type: binary              # binary | threshold
    modality: <api|web|mobile, must be allowed by charter>
    text: "..."
    trace:
      - ref: <type>:<signal-id-or-lib-path>
        quote: "..."          # optional, must appear verbatim in the committed source
review_brief:
  verify_first: []
  assumptions: []              # each: id, text, origin (signal | overview | library | inferred)
  open_questions: []
brief_ack: null                # the PM sets this, never you
---
```

## Output: the Review Brief

Place this at the top of the Thread file (and mirror the structured version into `review_brief` in the Spec frontmatter):

- **Verify first:** the 3 to 5 items most likely to be wrong or most costly if wrong.
- **Assumptions:** every assumption you made, each tagged with its origin — `signal`, `overview`, `library`, or `inferred`.
- **Open questions:** anything you could not resolve, each with a status.
- **Skipped:** which stages were bypassed (Framing, Validating), what was drafted in their place, which supporting artifacts weren't made, and who should review the draft.
- **Caution flag (optional):** state plainly if this looks risky for a fast track, then proceed anyway.

Do not set `brief_ack` yourself — that is the PM's single checkpoint. Tell the PM the Brief is ready for review and stop.

If a **Verify first** item needs an outside action rather than just a read-through (a meeting, a confirmation from someone else), also add it to the Thread's `## Open items` section — the Review Brief itself only lives until `brief_ack`, but `## Open items` persists and keeps surfacing in `whats-next` until the PM checks it off.

## What you must not do

- Do not mark the Thread or Spec as compiled, passed, or ready for engineering — that is `compile-check`'s job, not yours, and only the PM sets `status: Specified`, after a passing `compile-check`.
- Do not write to `signals/*/raw/`.
- Do not fabricate trace targets to satisfy the "every criterion needs a trace" rule — an uncovered claim is an open question, not a reason to invent a source.
