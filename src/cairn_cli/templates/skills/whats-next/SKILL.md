---
name: "whats-next"
description: "Look at a Thread's current state, track, and flags, and say in plain language what can happen next and which skill covers it — the single entry point so the PM never has to memorize Cairn's skill names."
argument-hint: "thread id (optional — defaults to the most recently touched Thread)"
metadata:
  product: cairn
  source: "docs/spec-as-code-revision.md Part 1 section 4 (Thread Lifecycle)"
user-invocable: true
disable-model-invocation: false
---

## What this does

The navigator. Reads one Thread (or, with no argument, finds the most recently modified Thread file) and answers "what do I do with this?" by matching its `state`, `track`, and any flags against the table below. It is a lookup, not a new gate — it never changes the Thread.

## Required inputs

1. The Thread file (or, with no argument given, the most recently modified file under `threads/`).
2. `charter.yaml`, to know the profile (`solo`/`team`) for any Warn/Error framing in its answer.

## Lookup table

| Thread state | Track | Flags | What's next |
|---|---|---|---|
| `Signal` | — | — | `shape-thread` (or `fast-track` if the PM wants to skip ahead) |
| `Shape` | — | mid-decision | `shape-thread` wasn't finished — resume it; the PM still owes a proceed/hold/drop call |
| `Feasibility` | normal | no `verdict_ref` | `assess-thread` |
| `Feasibility` | normal | `verdict_ref` present, no Spec yet | `spec-generator` |
| `Feasibility` | normal | Spec drafted, not compiled | `compile-check` |
| any | fast | no Review Brief yet | `fast-track` |
| any | fast | Review Brief exists, `brief_ack` unset | `ack-brief` |
| any | fast | `brief_ack` set, not compiled | `compile-check` |
| `Contract` | — | just kicked back by eng | `record-kickback`, then `revise-spec` |
| `Contract` | — | compiled, nothing else pending | tell the PM it's ready for `Launched` (enablement + eng acceptance — outside this skillset) |
| `Parked` / `Rejected` | — | — | nothing pending; mention the recorded reason so it isn't re-argued from scratch |
| any | — | PM asked for something off the core flow | name the matching optional skill (`jury-duty`, `bundle-threads`, `record-approval`, `readiness-check`, `theme-extractor`, `intake-signal`, `onboard-product`, `park-or-reject`) |

## Rules

1. Answer in plain language first ("this Thread needs a jury verdict before it can get a Spec draft"), then name the skill.
2. If more than one thing is technically valid (e.g., a Thread that could fast-track or go through the normal core flow), say so and let the PM choose — never pick for them.
3. If the Thread is missing fields the lookup needs (`state` itself, for instance), say that plainly rather than guessing.

## What you must not do

- Do not invoke the next skill yourself — name it and stop. The PM decides when to act.
- Do not change the Thread file.
