---
name: "assess-thread"
description: "Run a Thread through its Framing-stage critique: default to the jury (Advocate/Skeptic/Judge), map every edge case to a criterion or a deferral, record the verdict a Spec draft will depend on, and move the Thread to Validating."
argument-hint: "thread id to assess"
metadata:
  product: cairn
  source: "docs/spec-as-code-revision.md Part 1 section 4 (Thread Lifecycle) and section 8 (Trust Model, Jury)"
user-invocable: true
disable-model-invocation: false
---

## What this does

Step 2 of the core flow. Runs while a Thread is in `stage: Framing` (set by `shape-thread`) — the stage where the PM is talking to others to find what needs thinking about. Produces a `verdict_ref`: a critique that finds the real edge cases and risks, with each one mapped to a future acceptance criterion or explicitly deferred with a reason. `draft-spec` reads this verdict next, and `check-spec`'s C11 checks that every edge case it lists is accounted for.

When every edge case is mapped or deferred and the PM accepts the verdict, set `stage: Validating`: the Thread moves on to getting everyone on board (reviews, UX mocks, an API spec). This skill never sets `status: Specified` — that follows a passing `check-spec`, applied by the PM.

## Required inputs

1. The Thread file — must already be `stage: Framing`, `status: Active`. If it isn't, stop and say so; point the PM at `shape-thread` or `fast-track` instead.
2. `charter.yaml`.
3. Every signal file the Thread references, and every `architecture/<system>/overview.md` for systems in `touches`.
4. The problem-and-impact brief already on the Thread (from Exploring).

## Rules

1. **Default mechanism is the jury**, run via `jury-duty`: Advocate argues the case, Skeptic (on a different model from the Advocate; a coin flip from `cairn jury-draw` decides which gets which) attacks it for concrete edge cases, Judge renders a verdict. Do not reimplement the critique here — call `jury-duty` so the standalone and in-flow uses never drift apart. In Claude Code it runs the jurors as separate agents; elsewhere it plays the seats inline and says so.
2. Every edge case the jury raises gets mapped to a future criterion (named, not yet fully drafted — that's `draft-spec`'s job) or explicitly deferred with a reason. An edge case with neither is not allowed to close out. When a deferral still needs someone to make a call later (an accessibility level, a legal review, a pricing choice), ask the PM whether to mark it `needs_decision: true` with a `resurface_at`, so it comes back instead of being forgotten.
3. Never invent risks that aren't grounded in the signal, overview, or library content — label anything inferred as `inferred`, the same origin-tagging `fast-track` uses for assumptions.
4. If an overview a system in `touches` depends on is missing or unverified (`verified: false`), say so as part of the verdict — don't silently assess against unverified material.
5. **Scope check.** If the Thread now covers two or more outcomes that could each ship on its own and has no `scope_decision`, or has grown since one was recorded, or recorded `deferred`, run the scope check from `shape-thread`'s Scope check section: name the parts and offer the same three choices, defaulting to one Thread that hands off several Specs. Ask the Judge to give a view on scope as part of the verdict when it's `deferred`, and get the PM to resolve `deferred` to `single`, `multi_spec` or `split` before the Thread moves to Validating: draft-spec won't start without it.
6. **Before the jury runs**, if the Thread changes a user-facing flow and has no `journey:` in `outbound_refs`, offer `map-journey` once: a journey gives the Skeptic concrete steps and failure points to attack. If the PM declines, carry on. If the jury turns up another Thread with the same problem, offer `bundle-threads`.
7. Mark everything you write as agent-drafted.
8. **The Judge must have run.** Save jury-duty's transcript and the Judge's YAML to `threads/<thread_id>-verdict.md` and copy its `jury_seats` onto the Thread. If `jury_seats` has no `judge` entry, the gate stays shut: don't move the Thread to Validating and don't write a verdict yourself. Rerun `jury-duty`. `cairn check` fails a normal-track Spec whose Thread lacks the Judge seat or the verdict file (C28).

## Output

Append to the Thread file:

```yaml
stage: Validating          # only once every edge case is mapped or deferred and the PM accepts
verdict_ref: threads/<thread_id>-verdict.md   # the Judge's YAML plus the transcript jury-duty returned, verbatim
jury_seats: [...]          # from jury-duty, as returned: advocate, skeptic and judge, each with model and calls
jury_mode: agents | agents (same model) | inline   # from jury-duty; anything but `agents` means the Advocate and Skeptic shared a model
jury_models: {advocate: ..., skeptic: ..., judge: ..., draw: coin | fixed | config, seed: ...}   # from jury-duty; omit when inline
edge_cases:
  - id: EC-01                # an inferred trace in the Spec points here via `assumption`
    text: "..."
    mapped_to: <planned criterion name>   # or:
    deferred: true
    reason: "..."
    needs_decision: true     # optional: deferred, but someone still has to decide it (e.g. accessibility level)
    resurface_at: Validating | handoff | <YYYY-MM-DD>   # required with needs_decision: when to raise it again
    decision: null           # filled when decided: what was decided, by whom, on what date
    origin: signal | overview | library | inferred
    planned_spec: <key>      # only when the Thread has planned_specs: which part this edge case belongs to
```

Plus the verdict body: the edge cases found, each tagged with its origin.

If the Thread has `planned_specs`, propose which planned Spec each edge case belongs to (from each part's `outcome` and `covers`) and let the PM confirm, so `draft-spec` doesn't have to sort them out later. An edge case that fits no part goes to the PM as a possible missing part.

When the Thread moves to Validating, tell the PM who should review the draft: the sponsor (`validated_by`) and the owner of each system in `touches` from its overview, flagging any owner that is `TBD` or missing. Add that as a line in the Thread's `## Open items` (draft-spec's "Review reminder" section has the format), along with any supporting artifacts (UX mocks, an API spec) the verdict says Validating will need. It's a reminder, never a gate.

## What you must not do

- Do not set `status: Specified`. That follows a passing `check-spec` report.
- Do not draft the Spec or its acceptance criteria — only name what a criterion will need to cover.
- Do not run a single-pass critique when the Thread is on the normal track — that shortcut belongs to `fast-track` only. Full three-round jury, every time, here.
