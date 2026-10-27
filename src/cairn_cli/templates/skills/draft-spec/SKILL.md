---
name: "draft-spec"
description: "Draft the Spec, or one of the several planned Specs, a Thread hands off, from a Thread already in Validating, using its full jury verdict and linked supporting artifacts — the normal-track equivalent of what fast-track does in light form."
argument-hint: "thread id, and optionally which planned Spec (its key) to draft"
metadata:
  product: cairn
  source: "docs/spec-as-code-revision.md Part 1 section 7 (Components, Skills) and Part 2 (Spec Frontmatter Contract)"
user-invocable: true
disable-model-invocation: false
---

## What this does

Step 3 of the core flow. Drafts `specs/<spec_id>.md` from a Thread already in `stage: Validating` with a recorded jury verdict (from `assess-thread`). This is where everything gets put together: the verdict and the supporting artifacts (UX mocks, an API spec) linked in `outbound_refs` — reference them, don't re-invent their detail. Add each new Spec to the Thread's `outbound_refs` (`spec:SPEC-NNN`). A Thread can hand off several Specs: draft one per entry in `planned_specs` (see `shape-thread`'s Scope check), each with its own `spec_id`, and note in each Spec which other Specs it depends on (from `depends_on`). Write each new `spec_id` back into its `planned_specs` entry and the `## Planned Specs` table. See "Drafting one of several planned Specs" below. This is the **normal-track** sibling of `fast-track`'s Spec draft — same output contract, but built from a full jury verdict instead of a backfilled single-pass critique, and with no Review Brief or `brief_ack` checkpoint (those are fast-track-only).

## Required inputs

1. The Thread file — must be `stage: Validating`, `status: Active` (it stays Active while any planned Spec is undrafted, even after another has been handed off), with a `verdict_ref` present (from `assess-thread`). Read every supporting artifact in `outbound_refs` that resolves to a file; for a link outside the repo, cite it but don't guess its contents. API specs (`api:` refs) must be OpenAPI 3.1: check for `openapi: 3.1.x` at the document root, and if it's another version or format, tell the PM rather than drafting against it. Endpoints, fields and limits in criteria may then trace to that document. If missing, stop and point the PM at `assess-thread` first.
2. `charter.yaml`.
3. Every signal file and `architecture/<system>/overview.md` the Thread references.
4. Every journey in `outbound_refs` (`journey:<id>`, from `map-journey`). Trace criteria to its steps (`journey:JRN-001#step-2`), and draw `error_states` and `empty_states` from the steps' failure and empty cases. Cover each step with a criterion or list it in `out_of_scope` (C26).
5. The Thread's `## Q&A`, `use_cases` and `candidate_criteria` (from `ask-me`). Turn each candidate into a real criterion, tracing it to its `qa-NN` entry (`thread:THRD-001#qa-07`) with `basis: decided` and `decided_by` set to the PM. Every in-scope use case needs at least one criterion.
6. If this Thread is part of a Bundle (`bundle_id` set), read every sibling Thread in `thread_ids` too — each needs its own slice(s) in the Spec(s) this produces.

## Rules (do not deviate)

0. **Scope check first.** Don't draft until the Thread has a `scope_decision` of `single`, `multi_spec` or `split`. If it has none, or `deferred`, run `shape-thread`'s Scope check now, record the PM's answer, and draft per that choice. If it says `single` but the draft is heading for four or more slices, ask the PM once whether it's really several Specs. Never split the Thread yourself. `cairn check` fails a Spec whose Thread has no resolved decision (C27).

1. Every acceptance criterion is `binary` or carries a `threshold` (metric, operator, number, unit), and has at least one `trace` entry to a real committed file. Quote the source where possible. Each trace carries a `basis` (`direct`, `interpreted`, `inferred`, `decided`) with its required field, as in `check-spec` C23; an `inferred` trace points `assumption` at an edge case or assumption id in the jury verdict. Never mark something `direct` that the source doesn't actually say.
2. Group criteria into ordered slices; each slice gets a one-line `verify` note.
3. Map every edge case from the jury verdict to a criterion, or carry its deferral forward into `open_questions`.
4. Never invent numbers, endpoints, field names, or limits. Ask the PM or list as an open question.
5. Describe observable behavior, not implementation.
6. Mark everything you write as agent-drafted.
7. No open questions remain unresolved at handoff: each is `answered`, `deferred` (with reason and owner), or `out_of_scope`.

## Drafting one of several planned Specs

When the Thread's `planned_specs` has more than one entry:

1. **Pick which to draft.** Use the key the PM named. Otherwise propose the next one in ship order that has no `spec_id` yet and whose `depends_on` Specs are at least drafted, and confirm with the PM. Draft one Spec per run unless the PM asks for more.
2. **Assign the shared material before drafting.** The jury's edge cases, `use_cases`, `candidate_criteria`, journey steps and Q&A entries belong to the whole Thread. Give each to one planned Spec, using each entry's `outcome` and `covers`, and record it on the item as `planned_spec: <key>` (in a journey file, `planned_spec` on the journey covers all its steps, and a step can override it). Only items with no `planned_spec` yet need assigning. List your proposed assignment in one short table and ask the PM to confirm it, flagging anything that fits two parts or none. An item that fits none is a sign of a missing part: say so rather than forcing it in.
3. **This Spec covers only its own items.** Required inputs 4 and 5 and rule 3 apply to the items assigned to this Spec. Every other item goes in this Spec's `out_of_scope` with a pointer to where it lives: `covered by planned Spec refine-and-share` (or `by SPEC-002` once drafted). `check-spec` counts those pointers as covered (C11, C26).
4. **Read the existing Specs, never edit them.** Read every Spec already drafted for this Thread. Don't duplicate their criteria, and don't contradict what they promise, especially one that's `specified` or `handed_off`. If this part needs one of them changed, stop and say so: that's a `revise-spec` on that Spec, which the PM starts.
5. **Record what this Spec depends on.** List `depends_on` Specs in `sections.dependencies` by `spec_id`, or by key if they aren't drafted yet.

## Output

Same frontmatter contract as `fast-track` (`docs/spec-as-code-revision.md` Part 2), with these differences:

```yaml
spec_id: SPEC-NNN
spec_status: drafted       # drafted | specified | handed_off; see shape-thread
planned_spec: <key>        # which planned_specs entry this is; omit for a single-Spec Thread
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

**Lineage line.** The first line of the Spec, and of the parent Thread's body (add or update it there too) body, under the frontmatter, shows where it sits so a reader doesn't need the design doc:

```markdown
**Lineage:** feedback:FDBK-001, idea:IDEA-004 → THRD-007 → SPEC-012, SPEC-013
```

Signals come from the Thread's `inbound_refs`, Specs from its `outbound_refs` (`spec:` entries only); write `→ (no Spec yet)` before any exists. In a Spec, list only this Spec on the right and only the signals its criteria trace to on the left. For a Bundle, list each originating Thread: `… → THRD-003 + THRD-004 → SPEC-012`. Update the line whenever those refs change. `cairn find <id>` prints the same chain from the files if the two ever disagree.


## Review reminder (required)

Every time, before you finish, add a review reminder to the Thread's `## Open items` if one isn't there, and repeat it in your reply to the PM:

```markdown
- [ ] Review the draft before handoff: <sponsor name> (sponsor), <owner name> (<system> owner), ...
```

- Name the sponsor from `validated_by` and the owner of each system in `touches`, taken from that system's `architecture/<system>/overview.md` `owner`.
- Where an owner is `TBD`, missing, or the overview doesn't exist, write `<system>: owner TBD` in the line and say so in the reply: nobody can check those constraints until someone is named.
- Nobody has to sign off; this is a reminder, never a gate. If the PM says nobody needs to review, write `- [x] Review: none needed (PM, <date>)` so the next skill doesn't add it again.

## What you must not do

- Do not mark the Spec as compiled or ready — that's `check-spec`'s job.
- Do not set `status: Specified` or `spec_status: specified` yourself. Each Spec you draft gets `spec_status: drafted`; the Thread stays `Active` (see `shape-thread`'s "Each Spec has its own status").
- Do not draft without a recorded jury verdict unless the Thread is explicitly `track: fast` (in which case use `fast-track`, not this skill).
- Do not write to `signals/*/raw/`, and never fabricate a trace target.
