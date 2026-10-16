# Thread fidelity stages

**Status**: Draft

## Problem

"Signal" named two things: the intake artifact under `signals/<type>/`, and the first state of a Thread. A PM reading "this Thread is in Signal" couldn't tell whether it was a Thread at all. The single `state` field also mixed two questions: how far the thinking has got (Shape, Feasibility, Contract) and whether the work is alive (Parked, Rejected, Launched).

## The model

```
signal(s) ──► Exploring ──► Framing ──► Validating ──► Spec
                 └────────── Thread ──────────┘   (outbound_refs)
```

- A **signal** is an artifact: an idea, quote, directive, bug report or proposal. It is never a stage.
- A **Thread** is created when the PM decides one or more signals are worth pursuing. It links to them through `inbound_refs`. The signal files are not consumed, so one signal can feed several Threads.
- A **Spec** is what the Thread hands off. Once it exists, the Spec is the artifact engineering works from, not the Thread. The Thread's `outbound_refs` point at its Spec(s); one Thread can produce more than one.

A Thread has two independent fields: `stage` (its fidelity) and `status` (whether it's being worked on).

### Stages

Stage names are activities: they say what's happening now. Each stage's gate is what must be true to **leave** it.

| Stage | What's happening | Exit gate | Skill |
|---|---|---|---|
| **Exploring** | The PM, alone, fleshing out an idea. | Entry check met (feedback: recurring theme; requirement/mandate/idea: named sponsor). Problem-and-impact brief written. PM decides to proceed. | `shape-thread` |
| **Framing** | The PM is talking to others to find what needs thinking about. The jury critique runs here. | Jury verdict recorded; every edge case mapped to a future criterion or deferred with a reason. | `assess-thread` |
| **Validating** | Getting everyone on board. Supporting artifacts get made: UX mocks, an API spec, and so on. | A Spec compiles clean. No sign-off is required (see Reviews). | `spec-generator` → `compile-check` |

Leaving Validating is the handoff: the Spec goes to engineering and the Thread's status becomes Specified. There is no "Specifying" stage; putting the Spec together is the act of leaving Validating.

### Reviews

Nobody has to sign off. In Validating, Cairn reminds the PM who should review the Spec draft before handoff: the signal's sponsor (`validated_by`) and the owner of each system in `touches`. The reminder goes in the Thread's `## Open items`, where the PM checks it off. It never blocks a stage or the handoff. An org rule with `enforcement: block` still blocks, as before.

Names, not numbers, go in Thread files: names carry meaning and survive a stage being added. The order is defined once in code (`STAGES` in `ledger.py`).

### Status

| Status | Meaning |
|---|---|
| **Active** | Being worked on. Default. |
| **Parked** | On hold, with a reason and what has to happen first (`pickup_when`). Keeps its stage. |
| **Rejected** | Dropped, with a reason and category. Keeps its stage. |
| **Specified** | Handed off: a compiled Spec went to engineering. Stage stays Validating. |

Only the PM sets `status: Specified`, after a passing `compile-check`.

### Thread frontmatter

```yaml
thread_id: THRD-NNN
stage: Exploring | Framing | Validating
status: Active | Parked | Rejected | Specified
owner: <name>
inbound_refs: ["idea:TODO-11"]          # the signal(s) it came from
outbound_refs: ["spec:SPEC-001", "mock:<url>", "api:<path>"]   # what it produced
light_stages: [Framing, Validating]     # fast track only
```

### Flows

- **Normal**: `shape-thread` (Exploring → Framing), `assess-thread` (Framing → Validating), `spec-generator` + `compile-check` (Validating → status Specified).
- **Fast track**: `fast-track` goes from Exploring to a drafted Spec in one pass. Framing and Validating are backfilled in light form and listed in `light_stages`; the Review Brief records what was skipped, including any reviews and supporting artifacts.
- **Kickback**: status goes from Specified back to Active; stage stays Validating. `record-kickback` → `revise-spec` updates the same Spec at a new revision.
- **Park / reject / resume**: change `status` only. Resume sets status back to Active at the same stage.

## Migration

`cairn ledger` reads Threads that still carry the old `state` field, mapping them as below. New and edited Threads use `stage` + `status`.

| Old `state` | `stage` | `status` |
|---|---|---|
| Signal, Shape | Exploring | Active |
| Feasibility | Framing (Validating if a jury verdict exists) | Active |
| Contract, Launched | Validating | Specified |
| Parked, Rejected | `parked_from`, or inferred from what's present | Parked / Rejected |

## Changed in this pass

- `README.md`: concepts, lifecycle, gate table, getting-started step 3. Line 16 no longer says a Thread "begins when a signal is captured".
- Skills: `shape-thread`, `assess-thread`, `spec-generator`, `compile-check`, `fast-track`, `record-kickback`, `revise-spec`, `park-or-reject`, `whats-next`, `bundle-threads`, `intake-signal`, `onboard-product`.
- `src/cairn_cli/ledger.py` and `cli.py`: stage/status with legacy fallback.
- `pilot/threads/THRD-001.md` and `pilot/specs/SPEC-001.md` (local only: `pilot/` is git-ignored).

Not changed: the long-form design docs under `docs/`, which still use the old names.

## Open questions

1. **`cairn handoff` as a template script.** Direction: `cairn handoff <spec-id> --to export|repo|in_place [--where ...]` does the fixed part, and a team-editable script does the delivery.
   - **Fixed part (Cairn):** checks the Spec's latest compile report passed; builds a package in `.cairn/handoff/<spec-id>/` holding the Spec and an `addendum/` with a copy of every supporting artifact in the Thread's `outbound_refs` (files in the repo are copied; URLs are downloaded where reachable, otherwise listed in `addendum/LINKS.md`); writes `handoff` on the Thread.
   - **Delivery (the team's script):** `cairn init` installs `.cairn/handoff.py` from a template, once, and never overwrites it, the same way it treats `charter.yaml`. Cairn calls it with the package path, `to` and `where`. The template's default: `export` zips the package, `repo` copies it into a local checkout of the target repo, `in_place` does nothing.
   - Not decided: whether `cairn handoff` also sets `status: Specified`, or only records `handoff` and leaves the status to the PM; how a Spec copied to another repo keeps a link back to its Thread (a `source:` line naming this repo and Thread id is the candidate).

## Decided

- **No sign-offs** (2026-10-15). Validating reminds the PM to have the draft reviewed; it never requires approval. This also settles fast track: it lists the reviews as not yet done in the Review Brief.
- **Cairn stops at handoff** (2026-10-16). Built, launched and enablement are not tracked by Cairn; whoever picks up the Spec owns that. When the PM sets `status: Specified`, they also record where the Spec went:

  ```yaml
  handoff:
    to: export | repo | in_place
    where: "<team, repo URL or path>"   # export / repo only
    on: <date>
  ```

  - **export**: the Spec is written out (with the supporting-artifact addendum, when that exists) and handed to a team.
  - **repo**: the Spec is sent to a different repo.
  - **in_place**: the Spec stays where it is for the spec-kit process to pick up (specify → plan → tasks → implement).
- **Supporting artifacts are copied into the handoff** (2026-10-16), as an addendum alongside the Spec, not just linked.
- **API specs are OpenAPI 3.1** (2026-10-16). An `api:` supporting artifact must be an OpenAPI 3.1 document (`openapi: 3.1.x` at its root). Anything else is flagged to the PM, not silently used.
