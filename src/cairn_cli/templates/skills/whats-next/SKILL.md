---
name: "whats-next"
description: "Look at a Thread's current state, track, and flags, and say in plain language what can happen next and which skill covers it — the single entry point so the PM never has to memorize Cairn's skill names. With no Thread id, also gives a project-wide status snapshot (thread counts by state, what was last touched) for a Monday-morning catch-up."
argument-hint: "thread id (optional — with none given, shows a project status snapshot plus the most recently touched Thread's next step)"
metadata:
  product: cairn
  source: "docs/spec-as-code-revision.md Part 1 section 4 (Thread Lifecycle)"
user-invocable: true
disable-model-invocation: false
---

## What this does

The navigator. Reads one Thread (named, or with no argument, the most recently modified Thread file) and answers "what do I do with this?" by matching its `state`, `track`, and any flags against the table below. It is a lookup, not a new gate — it never changes anything.

If there's no Thread yet because nothing has been captured as a signal — a raw quote, directive, or bug report that hasn't been written to `signals/` — that's `intake-signal`'s job, not this skill's. This skill only navigates Threads that already exist.

With no Thread id given, it also opens with a **project status snapshot** — this is the "I'm back on Monday, what's going on" view: how many Threads are in each state, which one was last touched and when, and any open checklist items waiting on the PM (per-Thread or project-wide — see Checklists below). The per-Thread next-step answer still follows, for the most recently touched Thread.

## Required inputs

1. The Thread file (named, or with no argument given, the most recently modified file under `threads/`). For the status snapshot: every file under `threads/`.
2. `charter.yaml`, to know the profile (`solo`/`team`) for any Warn/Error framing in its answer.
3. `checklist.md` at the product root, if present (project-wide checklist — see Checklists below).

## Project status snapshot (no Thread id given)

1. Read every file under `threads/`. Group by `state`, and report the count in each (e.g. "3 in Feasibility, 1 in Contract, 2 Parked").
2. Name the most recently modified Thread (by file mtime) and how long ago, and flag any Thread untouched for an unusually long time if one stands out — don't manufacture urgency where there isn't any.
3. Across all Threads, list any unchecked `## Open items` (see Checklists below) grouped by Thread — this is what's still waiting on the PM, not the agent.
4. If `checklist.md` exists at the product root, list its unchecked top-level items too.
5. Then answer the normal per-Thread lookup (below) for the most recently touched Thread, exactly as if it had been named explicitly.

## Checklists (PM-maintained, never written by the agent on its own)

Two levels, both plain `- [ ]` / `- [x]` Markdown, checked off by the PM like any todo list:

- **Per-Thread** (`## Open items` section in the Thread's own file): operational to-dos tied to *that* Thread's progress — "meet with Architect to validate AC-002," "set up a UX review." These travel with the Thread through its lifecycle and get surfaced by this skill's status snapshot and single-Thread lookup alike.
- **Project-wide** (`checklist.md` at the product root): goals or commitments that span or sit above individual Threads — "ship the new email feature by Monday." May reference Thread ids but isn't required to.

This skill only reads and reports these — it never checks an item off or adds one. Any skill drafting or updating a Thread (`shape-thread`, `fast-track`, `assess-thread`, `spec-generator`) may propose an `## Open items` entry when it surfaces a real action the PM needs to take, but the PM owns checking items off.

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
4. If the Thread has a `## Open items` section with unchecked boxes, list them alongside the lookup's answer — they're often the real blocker (e.g., "waiting on the Architect meeting") even when the skill-level next step is clear.

## What you must not do

- Do not invoke the next skill yourself — name it and stop. The PM decides when to act.
- Do not change the Thread file, add or check off a checklist item, or edit `checklist.md`.
