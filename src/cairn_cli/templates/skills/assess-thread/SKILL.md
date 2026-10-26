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

1. **Default mechanism is the jury**, run via `jury-duty`: Advocate argues the case, Skeptic (on a different model than Advocate/Judge) attacks it for concrete edge cases, Judge renders a verdict. Do not reimplement the critique here — call `jury-duty` so the standalone and in-flow uses never drift apart. In Claude Code it runs the jurors as separate agents; elsewhere it plays the seats inline and says so.
2. Every edge case the jury raises gets mapped to a future criterion (named, not yet fully drafted — that's `draft-spec`'s job) or explicitly deferred with a reason. An edge case with neither is not allowed to close out.
3. Never invent risks that aren't grounded in the signal, overview, or library content — label anything inferred as `inferred`, the same origin-tagging `fast-track` uses for assumptions.
4. If an overview a system in `touches` depends on is missing or unverified (`verified: false`), say so as part of the verdict — don't silently assess against unverified material.
5. Mark everything you write as agent-drafted.

## Output

Append to the Thread file:

```yaml
stage: Validating          # only once every edge case is mapped or deferred and the PM accepts
verdict_ref: <path to the verdict, or inline if short>
jury_mode: agents | agents (same model) | inline   # from jury-duty; anything but `agents` means the Skeptic shared a model
jury_models: {advocate: ..., skeptic: ..., judge: ...}   # from jury-duty; omit when inline
edge_cases:
  - id: EC-01                # an inferred trace in the Spec points here via `assumption`
    text: "..."
    mapped_to: <planned criterion name>   # or:
    deferred: true
    reason: "..."
    origin: signal | overview | library | inferred
```

Plus the verdict body: the edge cases found, each tagged with its origin.

If the verdict shows who should review the draft, or which supporting artifacts (UX mocks, an API spec) Validating will need, propose them as lines in the Thread's `## Open items`.

## What you must not do

- Do not set `status: Specified`. That follows a passing `check-spec` report.
- Do not draft the Spec or its acceptance criteria — only name what a criterion will need to cover.
- Do not run a single-pass critique when the Thread is on the normal track — that shortcut belongs to `fast-track` only. Full three-round jury, every time, here.
