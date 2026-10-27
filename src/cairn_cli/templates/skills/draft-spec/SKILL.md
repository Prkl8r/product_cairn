---
name: "draft-spec"
description: "Draft the Spec a Thread hands off, from a Thread already in Validating, using its full jury verdict and linked supporting artifacts — the normal-track equivalent of what fast-track does in light form."
argument-hint: "thread id to draft a Spec for"
metadata:
  product: cairn
  source: "docs/spec-as-code-revision.md Part 1 section 7 (Components, Skills) and Part 2 (Spec Frontmatter Contract)"
user-invocable: true
disable-model-invocation: false
---

## What this does

Step 3 of the core flow. Drafts `specs/<spec_id>.md` from a Thread already in `stage: Validating` with a recorded jury verdict (from `assess-thread`). This is where everything gets put together: the verdict and the supporting artifacts (UX mocks, an API spec) linked in `outbound_refs` — reference them, don't re-invent their detail. Add each new Spec to the Thread's `outbound_refs` (`spec:SPEC-NNN`). A Thread can hand off several Specs: draft one per entry in `planned_specs` (see `shape-thread`'s Scope check), each with its own `spec_id`, and note in each Spec which other Specs it depends on (from `depends_on`). Write each new `spec_id` back into its `planned_specs` entry and the `## Planned Specs` table. If the PM asks for only some parts now, draft those and leave the rest with `spec_id: null`. This is the **normal-track** sibling of `fast-track`'s Spec draft — same output contract, but built from a full jury verdict instead of a backfilled single-pass critique, and with no Review Brief or `brief_ack` checkpoint (those are fast-track-only).

## Required inputs

1. The Thread file — must be `stage: Validating`, `status: Active` (it stays Active while any planned Spec is undrafted, even after another has been handed off), with a `verdict_ref` present (from `assess-thread`). Read every supporting artifact in `outbound_refs` that resolves to a file; for a link outside the repo, cite it but don't guess its contents. API specs (`api:` refs) must be OpenAPI 3.1: check for `openapi: 3.1.x` at the document root, and if it's another version or format, tell the PM rather than drafting against it. Endpoints, fields and limits in criteria may then trace to that document. If missing, stop and point the PM at `assess-thread` first.
2. `charter.yaml`.
3. Every signal file and `architecture/<system>/overview.md` the Thread references.
4. Every journey in `outbound_refs` (`journey:<id>`, from `map-journey`). Trace criteria to its steps (`journey:JRN-001#step-2`), and draw `error_states` and `empty_states` from the steps' failure and empty cases. Cover each step with a criterion or list it in `out_of_scope` (C26).
5. The Thread's `## Q&A`, `use_cases` and `candidate_criteria` (from `ask-me`). Turn each candidate into a real criterion, tracing it to its `qa-NN` entry (`thread:THRD-001#qa-07`) with `basis: decided` and `decided_by` set to the PM. Every in-scope use case needs at least one criterion.
6. If this Thread is part of a Bundle (`bundle_id` set), read every sibling Thread in `thread_ids` too — each needs its own slice(s) in the Spec(s) this produces.

## Rules (do not deviate)

0. **Scope check first.** If the Thread covers two or more outcomes that could each ship on its own but has no `scope_decision`, or `scope_decision: deferred`, run `shape-thread`'s Scope check before drafting, and draft per the PM's choice. Never split the Thread yourself.

1. Every acceptance criterion is `binary` or carries a `threshold` (metric, operator, number, unit), and has at least one `trace` entry to a real committed file. Quote the source where possible. Each trace carries a `basis` (`direct`, `interpreted`, `inferred`, `decided`) with its required field, as in `check-spec` C23; an `inferred` trace points `assumption` at an edge case or assumption id in the jury verdict. Never mark something `direct` that the source doesn't actually say.
2. Group criteria into ordered slices; each slice gets a one-line `verify` note.
3. Map every edge case from the jury verdict to a criterion, or carry its deferral forward into `open_questions`.
4. Never invent numbers, endpoints, field names, or limits. Ask the PM or list as an open question.
5. Describe observable behavior, not implementation.
6. Mark everything you write as agent-drafted.
7. No open questions remain unresolved at handoff: each is `answered`, `deferred` (with reason and owner), or `out_of_scope`.

## Output

Same frontmatter contract as `fast-track` (`docs/spec-as-code-revision.md` Part 2), with these differences:

```yaml
spec_id: SPEC-NNN
spec_status: drafted       # drafted | specified | handed_off; see shape-thread
thread_id: THRD-NNN        # or bundle_id: BUNDLE-NNN, see bundle-threads
charter_version: <from charter.yaml>
generated_by:
  skill: draft-spec
  skill_version: 0.1.0
track: normal
# no skipped_gates, no review_brief, no brief_ack — those are fast-track-only
sections: {...}
slices: [...]
open_questions: [...]
criteria: [...]
```

If drafting for a Bundle, criteria carry the normal `trace` entries back to each originating Thread's signals — never a bundle-level trace.

After drafting, add a review reminder to the Thread's `## Open items` if one isn't there: who should read the draft before handoff — the sponsor (`validated_by`) and the owner of each system in `touches`, by name where the overview gives one. Nobody has to sign off; this is a reminder, never a gate.

## What you must not do

- Do not mark the Spec as compiled or ready — that's `check-spec`'s job.
- Do not set `status: Specified` or `spec_status: specified` yourself. Each Spec you draft gets `spec_status: drafted`; the Thread stays `Active` (see `shape-thread`'s "Each Spec has its own status").
- Do not draft without a recorded jury verdict unless the Thread is explicitly `track: fast` (in which case use `fast-track`, not this skill).
- Do not write to `signals/*/raw/`, and never fabricate a trace target.
