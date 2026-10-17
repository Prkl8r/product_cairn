---
name: "whats-next"
description: "Look at a Thread's current stage, status, track, and flags, and say in plain language what can happen next and which skill covers it — the single entry point so the PM never has to memorize Cairn's skill names. With no Thread id, also gives a project-wide status snapshot (thread counts by stage and status, what was last touched) for a Monday-morning catch-up."
argument-hint: "thread id (optional — with none given, shows a project status snapshot plus the most recently touched Thread's next step)"
metadata:
  product: cairn
  source: "specs/001-thread-fidelity-stages/spec.md"
user-invocable: true
disable-model-invocation: false
---

## What this does

The navigator. Reads one Thread (named, or with no argument, the most recently modified Thread file) and answers "what do I do with this?" by matching its `stage`, `status`, `track`, and any flags against the table below. It is a lookup, not a new gate — it never changes anything.

If there's no Thread yet because nothing has been captured as a signal — a raw quote, directive, or bug report that hasn't been written to `signals/` — that's `intake-signal`'s job, not this skill's. This skill only navigates Threads that already exist.

With no Thread id given, it also opens with a **project status snapshot** — this is the "I'm back on Monday, what's going on" view: how many Threads are in each stage, and how many are Parked, Rejected, Specified or Handed off, which one was last touched and when, and any open checklist items waiting on the PM (per-Thread or project-wide — see Checklists below). The per-Thread next-step answer still follows, for the most recently touched Thread.

## Required inputs

1. The Thread file (named, or with no argument given, the most recently modified file under `threads/`). For the status snapshot: every file under `threads/`.
2. `charter.yaml`, to know the profile (`solo`/`team`) for any Warn/Error framing in its answer.
3. `checklist.md` at the product root, if present (project-wide checklist — see Checklists below).

## Project status snapshot (no Thread id given)

1. Run `cairn ledger --json` rather than opening every file under `threads/` — it returns each Thread's stage, status, linked signals, and which Specs went to engineering in one compact call. Group Active Threads by `stage` and the rest by `status`, and report the counts (e.g. "3 Framing, 1 Validating, 1 Specified, 1 Handed off, 2 Parked"). Also mention signals with no Thread yet. Only open a Thread file itself when you need its `## Open items`. If `cairn` isn't installed, fall back to reading the files.
2. Name the most recently modified Thread (by file mtime) and how long ago, and flag any Thread untouched for an unusually long time if one stands out — don't manufacture urgency where there isn't any.
3. Across all Threads, list any unchecked `## Open items` (see Checklists below) grouped by Thread — this is what's still waiting on the PM, not the agent.
4. If `checklist.md` exists at the product root, list its unchecked top-level items too.
5. Then answer the normal per-Thread lookup (below) for the most recently touched Thread, exactly as if it had been named explicitly.

## Checklists (PM-maintained, never written by the agent on its own)

Two levels, both plain `- [ ]` / `- [x]` Markdown, checked off by the PM like any todo list:

- **Per-Thread** (`## Open items` section in the Thread's own file): operational to-dos tied to *that* Thread's progress — "meet with Architect to validate AC-002," "set up a UX review." These travel with the Thread through its lifecycle and get surfaced by this skill's status snapshot and single-Thread lookup alike.
- **Project-wide** (`checklist.md` at the product root): goals or commitments that span or sit above individual Threads — "ship the new email feature by Monday." May reference Thread ids but isn't required to.

This skill only reads and reports these — it never checks an item off or adds one. Any skill drafting or updating a Thread (`shape-thread`, `fast-track`, `assess-thread`, `draft-spec`) may propose an `## Open items` entry when it surfaces a real action the PM needs to take, but the PM owns checking items off.

## Lookup table

| Stage / status | Track | Flags | What's next |
|---|---|---|---|
| Exploring, Active | — | — | `shape-thread` (or `fast-track` if the PM wants to skip ahead) |
| Exploring, Active | — | brief drafted, no decision | `shape-thread` wasn't finished — resume it; the PM still owes a proceed/hold/drop call |
| Framing, Active | normal | no `verdict_ref` | `assess-thread` — and this is the stage to talk it through with others |
| Framing, Active | normal | `verdict_ref` present, edge cases unmapped | finish `assess-thread`; it moves the Thread to Validating |
| Validating, Active | normal | supporting artifacts or reviews still open | get everyone on board: list the open artifacts and review reminders from `## Open items`. Reviews never block |
| Validating, Active | normal | no Spec in `outbound_refs` | `draft-spec` |
| Validating, Active | normal | Spec drafted, not compiled | `check-spec` |
| Validating, Active | any | compiled clean | remind the PM once to have the draft reviewed if that item is unchecked, then say the PM can set `status: Specified` |
| Specified | — | — | ready to hand off with `cairn handoff <spec-id> --to export\|repo\|in_place` (export to a team, send to another repo, or leave in place for spec-kit). It packages the Spec with its supporting artifacts, sets `status: Handed off` and records `handoff` |
| any, Active | fast | no Review Brief yet | `fast-track` |
| any, Active | fast | Review Brief exists, `brief_ack` unset | `ack-brief` |
| any, Active | fast | `brief_ack` set, not compiled | `check-spec` |
| Handed off | — | kicked back by eng | `record-kickback`, then `revise-spec` |
| Handed off | — | nothing pending | say where (`handoff`). Build and launch belong to whoever received it, not Cairn |
| Parked | — | — | say what it's waiting on (`pickup_when`). If that has happened, or the PM wants it back, `park-or-reject` resumes it |
| Rejected | — | — | nothing pending; mention the recorded reason and `reject_category` so it isn't argued again from scratch |
| any | — | PM wants to stop or pause it | `park-or-reject` |
| any | — | looks related to another Thread, or PM says "these go together" | `bundle-threads` |
| any | — | PM asked for something off the core flow | name the matching optional skill (`bundle-threads`, `intake-signal`, `onboard`, `park-or-reject`). `jury-duty`, `readiness-check`, `record-approval` and `theme-extractor` aren't built yet: say so, and do the work inline if the PM wants it |

Threads written before stages existed may still carry a single `state` field. Read it as: Signal/Shape → Exploring; Feasibility → Framing; Contract/Launched → Handed off; Parked/Rejected → that status. Mention once that the Thread uses the old field.

## Rules

1. Answer in plain language first ("this Thread needs a jury verdict before it can get a Spec draft"), then name the skill.
2. If more than one thing is technically valid (e.g., a Thread that could fast-track or go through the normal core flow), say so and let the PM choose — never pick for them.
3. If the Thread is missing fields the lookup needs (`stage` or `status`, for instance), say that plainly rather than guessing.
4. If the Thread has a `## Open items` section with unchecked boxes, list them alongside the lookup's answer — they're often the real blocker (e.g., "waiting on the Architect meeting") even when the skill-level next step is clear.

## What you must not do

- Do not invoke the next skill yourself — name it and stop. The PM decides when to act.
- Do not change the Thread file, add or check off a checklist item, or edit `checklist.md`.
