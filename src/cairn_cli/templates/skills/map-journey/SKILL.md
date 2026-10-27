---
name: "map-journey"
description: "Map the user journey a Thread changes, step by step: the user's goal, what the system does, and what happens when it fails or has nothing to show. Each step is traced to a signal or overview or labelled inferred. Run it in Framing to give the jury something concrete to attack, or in Validating as a supporting artifact the Spec traces to."
argument-hint: "thread id, and optionally which journey (e.g. \"first-time import\")"
metadata:
  product: cairn
  source: "README (Validating supporting artifacts); check-spec C10, C23 and C26"
user-invocable: true
disable-model-invocation: false
---

## What this does

Drafts `journeys/<journey_id>.md`: the path a user takes through the part of the product a Thread changes, one step at a time. Each step says what the user is trying to do, what they do, what the system does, and what they see when it fails or has nothing to show. The journey is a supporting artifact, like a UX mock or an API spec: it's added to the Thread's `outbound_refs` as `journey:<journey_id>`, `draft-spec` traces criteria to its steps, and `cairn handoff` copies it into the package engineering receives.

It's optional. A Thread with no user-facing flow (a back-end job, an API-only change) doesn't need one; say so and stop.

**When to run it:**
- **Framing:** a rough journey before or alongside `assess-thread`, so the jury attacks concrete steps rather than a paragraph. Edge cases the jury finds often become new error or empty states on a step.
- **Validating:** firm it up so `draft-spec` can trace criteria to it and fill `error_states` and `empty_states` from it.
- **Fast track:** `fast-track` can call it in light form (happy path plus the error states the signal mentions). Steps it adds are tagged as in any other run.

## Required inputs

1. The Thread file. Any stage up to Validating with `status: Active`; for a Thread that's Specified or Handed off, stop and point at `record-kickback`/`revise-spec`, since changing the journey changes the Spec.
2. `charter.yaml`, for `modality` and `ui_presence`. If `ui_presence: false`, the journey is the API consumer's (the calls a client makes, in order), not screens.
3. Every signal in the Thread's `inbound_refs`, and the overview for each system in `touches`.
4. Any supporting artifacts already in `outbound_refs` (UX mocks, an API spec). Reference them from steps; don't restate their detail.
5. The jury verdict, if there is one (`verdict_ref`), so its edge cases can land on steps.

Ask the PM which user and which goal if the Thread covers more than one. One journey per user goal; a Thread can have several (`journey:JRN-001`, `journey:JRN-002`). If the Thread has `planned_specs`, say which planned Spec each journey serves.

## Rules

1. **Describe what the user does and sees, never how it's built.** No frameworks, tables or internal services. Same line as `check-spec` C22.
2. **Every step carries an `origin`:** `signal`, `overview`, `library` or `inferred`, with a `source` ref for anything but `inferred` (same ref format as a Spec trace, e.g. `feedback:ZD-88421`). Quote the source where you can. Never mark a step `signal` that the signal doesn't describe.
3. **Inferred steps are allowed, but visible.** Fill gaps between known steps so the journey reads end to end, and tag each one `inferred`. If more than half the steps are inferred, say so at the top of the journey and in chat: the journey is a guess to check with users, not evidence.
4. **Map the current journey first when the Thread changes an existing flow.** Record it as `current` and the proposed one as `proposed`, so the change is visible. For a new flow, only `proposed`.
5. **Every step names its failure and empty cases,** or writes `none: <reason>`. These feed the Spec's required `error_states` and `empty_states` sections (C10). Use only what the signals, overviews or jury verdict support; anything else is `inferred`.
6. **Never invent numbers, copy, field names or limits.** Ask the PM or record an open question.
7. **Mark the file agent-drafted** until the PM edits or accepts it (`accepted_by`).

## Output

`journeys/<journey_id>.md`, where `journey_id` is the next free `JRN-NNN`:

```yaml
---
journey_id: JRN-001
thread_id: THRD-001          # or bundle_id
planned_spec: core           # optional: the planned_specs key this journey serves
persona: "..."               # who, from the signal or overview; "unknown" if neither says
goal: "..."                  # what they're trying to get done
modality: web | mobile | api | cli
variant: proposed            # current | proposed
agent_drafted: true
accepted_by: null            # the PM sets this, never you
steps:
  - id: step-1               # the anchor a Spec trace points at: journey:JRN-001#step-1
    user_goal: "..."
    user_action: "..."
    system_response: "..."
    error_states: ["..."]    # or ["none: <reason>"]
    empty_states: ["..."]    # or ["none: <reason>"]
    edge_cases: [EC-02]      # ids from the jury verdict that land on this step, if any
    artifacts: ["mock:design/screens/import.png"]   # optional
    origin: signal           # signal | overview | library | inferred
    source: feedback:ZD-88421
    quote: "..."             # optional, verbatim from the source
open_questions: []           # each: text, owner
---
```

Under the frontmatter, write the journey as a short numbered list a person can read in a minute, and for a `current`/`proposed` pair, one line on what changed.

Then, on the Thread:
- Add `journey:<journey_id>` to `outbound_refs`.
- If a step surfaced something the PM must do outside the tool (check a step with real users, get a mock made for a step), add it to `## Open items`.
- If a step's error or empty state looks like a risk the jury didn't raise and the Thread is still in Framing, mention it so the PM can bring it to `assess-thread`.

## How the Spec uses it

`draft-spec` and `fast-track` trace criteria to steps with `ref: journey:JRN-001#step-2` and the normal `basis` rules (C23). A step tagged `inferred` can't back a `direct` trace. `check-spec` C26 warns when a step in a journey the Spec covers has no criterion tracing to it and isn't listed in the Spec's `out_of_scope`.

## What you must not do

- Do not change the Thread's stage or status.
- Do not draft acceptance criteria; that's `draft-spec`'s job. A step says what happens, not how to test it.
- Do not edit a journey on a Specified or Handed-off Thread without the PM starting a revision.
- Do not write to `signals/*/raw/`, and never fabricate a source.
