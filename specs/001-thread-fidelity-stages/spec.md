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

Leaving Validating takes two steps: the Spec compiles clean (status Specified), then it goes out (status Handed off). There is no "Specifying" stage; putting the Spec together is the act of leaving Validating.

### Reviews

Nobody has to sign off. In Validating, Cairn reminds the PM who should review the Spec draft before handoff: the signal's sponsor (`validated_by`) and the owner of each system in `touches`. The reminder goes in the Thread's `## Open items`, where the PM checks it off. It never blocks a stage or the handoff. An org rule with `enforcement: block` still blocks, as before.

Names, not numbers, go in Thread files: names carry meaning and survive a stage being added. The order is defined once in code (`STAGES` in `ledger.py`).

### Status

| Status | Meaning |
|---|---|
| **Active** | Being worked on. Default. |
| **Parked** | On hold, with a reason and what has to happen first (`pickup_when`). Keeps its stage. |
| **Rejected** | Dropped, with a reason and category. Keeps its stage. |
| **Specified** | The Spec exists and compiles clean; not sent anywhere yet. Stage stays Validating. |
| **Handed off** | The Spec went out (see Decided: handoff). Stage stays Validating. |

Only the PM sets `status: Specified`, after a passing `compile-check`. `Handed off` is set when the handoff is recorded.

### Thread frontmatter

```yaml
thread_id: THRD-NNN
stage: Exploring | Framing | Validating
status: Active | Parked | Rejected | Specified | Handed off
owner: <name>
inbound_refs: ["idea:TODO-11"]          # the signal(s) it came from
outbound_refs: ["spec:SPEC-001", "mock:<url>", "api:<path>"]   # what it produced
light_stages: [Framing, Validating]     # fast track only
```

### Flows

- **Normal**: `shape-thread` (Exploring → Framing), `assess-thread` (Framing → Validating), `spec-generator` + `compile-check` (Validating → status Specified), then handoff (status Handed off).
- **Fast track**: `fast-track` goes from Exploring to a drafted Spec in one pass. Framing and Validating are backfilled in light form and listed in `light_stages`; the Review Brief records what was skipped, including any reviews and supporting artifacts.
- **Kickback**: status goes from Handed off back to Active; stage stays Validating. `record-kickback` → `revise-spec` updates the same Spec at a new revision.
- **Park / reject / resume**: change `status` only. Resume sets status back to Active at the same stage.

## Migration

`cairn ledger` reads Threads that still carry the old `state` field, mapping them as below. New and edited Threads use `stage` + `status`.

| Old `state` | `stage` | `status` |
|---|---|---|
| Signal, Shape | Exploring | Active |
| Feasibility | Framing (Validating if a jury verdict exists) | Active |
| Contract, Launched | Validating | Handed off |
| Parked, Rejected | `parked_from`, or inferred from what's present | Parked / Rejected |

## Changed in this pass

- `README.md`: concepts, lifecycle, gate table, getting-started step 3. Line 16 no longer says a Thread "begins when a signal is captured".
- Skills: `shape-thread`, `assess-thread`, `spec-generator`, `compile-check`, `fast-track`, `record-kickback`, `revise-spec`, `park-or-reject`, `whats-next`, `bundle-threads`, `intake-signal`, `onboard-product`.
- `src/cairn_cli/ledger.py` and `cli.py`: stage/status with legacy fallback.
- `src/cairn_cli/handoff.py`, `templates/handoff.py`, `tests/test_handoff.py`: the handoff command.
- `pilot/threads/THRD-001.md` and `pilot/specs/SPEC-001.md` (local only: `pilot/` is git-ignored).

Not changed: the long-form design docs under `docs/`, which still use the old names.

## Handoff command

Built: `cairn handoff <spec-id> --to export|repo|in_place [--where ...] [--dry-run]`.

- **Cairn's part:** refuses unless the Thread is Specified and the compile report has `## Verdict: Pass`. Builds `.cairn/handoff/<spec-id>/` (git-ignored) with `spec.md` (the Spec plus its `source` link), `addendum/` (copies of every supporting artifact in the Thread's `outbound_refs`: repo files copied, downloadable URLs fetched, the rest listed in `addendum/LINKS.md`) and `manifest.json`. Warns when an `api:` artifact isn't OpenAPI 3.1. Then runs the delivery script, and only if it succeeds sets `status: Handed off` and writes `handoff`.
- **Delivery (the team's script):** `cairn init` installs `.cairn/handoff.py` from a template, once, and never overwrites it, even with `--force`. The default: `export` zips the package, `repo` copies it into `<checkout>/specs/<spec-id>/` of a local checkout of the target repo, `in_place` does nothing. A non-zero exit leaves the Thread Specified.
- The source link is added only to the packaged copy; the Spec in this repo is unchanged:

  ```yaml
  source:
    repo: <this repo's remote URL, or its path if it has none>
    thread_id: THRD-NNN
  ```

- The Thread's `handoff` records `to`, `where` (export/repo only), `on`, `spec_id` and `revision`.

## Decided

- **No sign-offs** (2026-10-15). Validating reminds the PM to have the draft reviewed; it never requires approval. This also settles fast track: it lists the reviews as not yet done in the Review Brief.
- **Cairn stops at handoff** (2026-10-16). Built, launched and enablement are not tracked by Cairn; whoever picks up the Spec owns that. When the Spec goes out, the Thread's status becomes `Handed off` and `handoff` records where it went:

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
