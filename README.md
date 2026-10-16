# Cairn

*Threading the needle: just-in-time requirements, from signal to Spec.*

Cairn is a Markdown-and-YAML workflow for turning raw product signal (feedback, requirement docs, mandates, ideas) into an engineering-ready Spec, without the LLM hallucinating claims no one can check. A cairn is a trail marker — it shows the way without walking it for you. The PM drives, the agent drafts and critiques, and nothing runs unless the PM asks for it.

**Flow: Signals → Threads → Specs.** One or more signals feed a Thread. The PM creates a Thread from one or more signals, and it moves through three stages of rising fidelity (Exploring, Framing, Validating) until it hands off one or more Specs that engineering (or a coding agent) picks up.

---

## Core concepts

| Term | What it is |
|---|---|
| **Signal** | An artifact, never a stage: raw input that feeds a Thread: `feedback` (tickets, Slack), `requirement` (a doc from another team), `mandate` (a compliance/exec directive), or `idea`. Lives at `signals/<type>/<id>.md`. |
| **Thread** | The unit of work. Begins when the PM decides one or more signals are worth pursuing; links to them in `inbound_refs` (signals aren't consumed, so one can feed several Threads) and to what it produced in `outbound_refs`. Has a `stage` (how far the thinking has got) and a `status` (whether it's being worked on). Lives at `threads/<id>.md`. Required frontmatter is only `thread_id`, `stage`, `status`, `owner` — a Thread can be one signal and a paragraph. |
| **Spec** | What a Thread hands off when it leaves Validating — from then on, the artifact engineering works from. Listed in the Thread's `outbound_refs`. One Thread can produce more than one Spec. Lives at `specs/<id>.md`. |
| **Charter** (`charter.yaml`) | The product's root boundaries: modality, UI presence, profile (`solo`/`team`), write authority, data classification, org rules. Constrains a Thread; never starts one. |
| **Architecture overview** (`architecture/<system>/overview.md`) | What a system owns, its interfaces, dependencies, constraints, known quirks. Readiness: **L0** uncharted, **L1** drafted/imported, **L2** verified by a named owner. Loaded into context only when a Thread's `touches` names that system. |
| **Track** | `normal` (every stage, full jury) or `fast` (skip Framing/Validating, backfill them lightly, write a Review Brief). Either way the compile check's traceability rules still apply. |

Gates are guardrails, not a prison. The PM can skip ahead (`fast-track`) or step around a check; the system never silently blocks, it tells you what you're skipping and what to verify.

---

## The lifecycle

```
signal(s) ──► Exploring ──► Framing ──► Validating ──► Spec
                 └────────── Thread ──────────┘   (outbound_refs)
```

**Stages** measure fidelity. Each name says what's happening now; each gate is what must be true to leave it.

| Stage | What's happening | Exit gate | Skill |
|---|---|---|---|
| **Exploring** | The PM, alone, fleshing out an idea. | Feedback: recurring theme met. Requirement/mandate/idea: a named sponsor validated it. Problem-and-impact brief written; PM decides **proceed**. | `shape-thread` |
| **Framing** | Talking to others to find what needs thinking about. The jury runs here. | Jury verdict recorded; every edge case mapped to a criterion or deferred. | `assess-thread` |
| **Validating** | Getting everyone on board; UX mocks, an API spec (OpenAPI 3.1) and other supporting artifacts get made. | The Spec compiles clean. No sign-off is required: Cairn reminds the PM who should review the draft (the sponsor, owners of systems in `touches`), and never blocks on it. | `spec-generator` → `compile-check` |

Leaving Validating is the handoff: the PM sets `status: Specified` and the Spec goes to engineering.

**Status** is separate from stage, so a Thread keeps its stage when it stops:

| Status | Meaning | Skill |
|---|---|---|
| **Active** | Being worked on (default). | — |
| **Parked** | On hold, with what has to happen first (`pickup_when`). | `park-or-reject` |
| **Rejected** | Dropped, with a reason and category. | `park-or-reject` |
| **Specified** | Handed off to engineering. | PM, after a passing `compile-check` |

- **Kickback**: engineering sends the Spec back. Status returns to Active at Validating; `record-kickback` → `revise-spec` updates the same Spec.
- **Fast track**: `fast-track` goes from Exploring to a drafted Spec, backfilling Framing and Validating lightly (`light_stages`), with a Review Brief and one acknowledgement.
- **Handoff** ends Cairn's part. The PM records where the Spec went in `handoff`: exported to a team, sent to another repo, or left in place for spec-kit to pick up. Whoever receives it tracks build and launch (see `specs/001-thread-fidelity-stages/spec.md`).

---

## Getting started

**0. Install Cairn into your product repo.**

```
pip install -e /path/to/product_cairn   # or: pip install -e . from inside this repo
cd /path/to/your-product-repo
cairn init --here                       # or: cairn init <new-project-name>
```

This copies the `.claude/skills/` into the target repo, creates the `signals/`, `threads/`, `specs/`, `architecture/`, `library/` skeleton, writes a `charter.yaml` template, and pins the installed version in `.cairn/package.lock`. It's idempotent — rerunning `cairn init` never overwrites `charter.yaml` or anything you've already written; pass `--force` to refresh the skill files themselves after an update. Run `cairn doctor` any time to check the install is complete.

Two read-only commands show what's been asked and what's shipped. Neither keeps an index; both rescan the files each run:

```bash
cairn ledger              # every signal (and whether a Thread picked it up), Threads by stage and status, Specs sent to engineering
cairn find "roster csv"   # keyword search across signals, threads, specs, library/, architecture/ (--kind to narrow)
cairn find ZD-88421       # an exact id shows its full lineage: signals -> thread -> specs -> referenced docs
```

Add `--json` to either command for compact output that scripts, CI, or another agent can read without opening the repo's files. The skills use the same commands to keep their token use down.

For people who don't have Cairn installed, `cairn snapshot` writes `STATUS.md` (a readable table) and `STATUS.json` at the repo root. Commit them, and anyone with read access can check status. To keep them current on every commit, add the pre-commit hook. This works on a new or an existing install, and it leaves any hook you already have in place:

```bash
cairn init --here --status-hook
```

The hook does nothing on machines where `cairn` isn't installed, so it won't block a teammate's commits.

`--json` and `snapshot` leave out anything marked `data_class: restricted`, including the ids of restricted signals, unless you pass `--include-restricted`. Plain terminal output shows everything and tags restricted items. Every output lists broken references (a Thread or Spec pointing at a signal, Thread, or library file that doesn't exist), and `cairn doctor` warns about them.

**1. Onboard the product, once.** Nothing else works without a ratified `charter.yaml` and at least an L1 overview for the systems a Thread will touch:

```
onboard-product            # brownfield: pulls from the codebase and/or a connected tracker
onboard-product --new      # greenfield: runs an interview instead
```

**2. Capture a signal.** Write it to `signals/<type>/<id>.md` (redacted/committed) with a raw copy under `signals/<type>/raw/` (git-ignored).

**3. Start a Thread.** Minimal frontmatter — `thread_id`, `stage: Exploring`, `status: Active`, `owner`, `inbound_refs`, `touches` — plus one paragraph of what this is and why it matters.

**4. Move it.** Either walk the core flow (below) or say "take this to Spec" for `fast-track`.

**5. Lost?** Run `whats-next` on any Thread — it reads the stage and status and tells you, in plain language, which skill to run next.

---

## The core flow

Four skills, run in order, cover the normal track end to end:

1. **`shape-thread`** — Exploring → Framing (or Parked/Rejected). Checks the entry gate, drafts a problem-and-impact brief, gets the PM's proceed/hold/drop call.
2. **`assess-thread`** — The Framing-stage critique, then Framing → Validating. Runs the Advocate/Skeptic/Judge jury, maps every edge case to a future criterion or a deferral, records the verdict.
3. **`spec-generator`** — Drafts the Spec from a Validating Thread's jury verdict: binary-or-thresholded criteria, each traced to a real source, grouped into verifiable slices.
4. **`compile-check`** — The deterministic gate. Checks structure, traceability, criteria quality, slices, and that no open question is left hanging — by hand, standing in for the `mcp-spec-compiler` server that doesn't exist yet. No LLM judgment calls on correctness, only well-formedness.

**The loop-back**, for when engineering sends a Spec back: **`record-kickback`** logs why and sets the Thread's status back to Active (it stays in Validating); **`revise-spec`** redrafts only the affected slices under the *same* `spec_id` at a bumped `revision`, so it reads as an update, not a new document.

**The shortcut**: **`fast-track`** jumps straight from Exploring to a drafted Spec, backfilling Framing and Validating in light form (a short brief, a single-pass critique instead of the full jury) and writing a **Review Brief** — verify-first items, every assumption tagged by origin (`signal`/`overview`/`library`/`inferred`), open questions, and what was skipped. One acknowledgement (`brief_ack`) is the only checkpoint; `compile-check` still enforces everything else.

**The navigator**: **`whats-next`** is a lookup, not a gate. Point it at a Thread (or nothing, for the most recently touched one) and it names the one thing to do next — so nobody has to memorize this table.

**The prerequisite**: **`onboard-product`** is the one entry point before any Thread can exist. Brownfield, it pulls context itself — scanning a codebase (READMEs, manifests, directory layout, OpenAPI/schema files, infra config) and/or querying a connected tracker (Jira, Linear, ClickUp, Monday, Asana) — rather than waiting for the PM to hand it docs. Greenfield (`--new`), it runs a structured interview and leaves unanswered fields as visible `TBD`. Either way it never self-verifies: every overview it produces starts at L1, and only a named human can promote one to L2.

Everything an agent drafts is marked agent-drafted until the PM edits or accepts it. Nothing above changes a Thread's stage or status or writes a file without the PM asking.

---

## Repo layout

```
charter.yaml                     # product root boundaries (from onboard-product)
signals/<type>/<id>.md           # committed, redacted signal
signals/<type>/raw/<id>.*        # git-ignored raw copy
threads/<id>.md                  # one Thread per unit of work
specs/<id>.md                    # compiled output, one or more per Thread
specs/<id>.compile_report.md     # compile-check's output for that Spec
architecture/<system>/overview.md  # one per system a Thread can `touches`
library/                         # historical specs, compliance docs (optional)
.claude/skills/                  # the skills documented above
docs/
  spec-as-code-master-document.md  # the PRD: outcomes, behavior, metrics
  spec-as-code-revision.md         # full lifecycle, compile-check rules, install/update design
  cairn-pilot-walkthrough.md       # a by-hand dry run of fast-track, no tooling
pilot/                            # a worked example: one real signal through fast-track
```

---

## Roadmap: what's not built yet

The core flow above is complete. Still missing, named today only as placeholders in `whats-next`'s own dispatch table:

- **Handoff tooling** — nothing yet writes the export package (Spec plus supporting-artifact addendum) or sends a Spec to another repo; the PM does it by hand and records it in `handoff`.
- **`onboard-product`'s onboarding is done**; the rest below are genuinely optional, built when a PM first asks for them:
  - `jury-duty` — the Advocate/Skeptic/Judge critique, as its own standalone skill (today it's only described inside `assess-thread`/`fast-track`).
  - `readiness-check` — the on-demand "is this ready for engineering?" qualitative review.
  - `record-approval` — recording/drafting an approval ask.
  - `theme-extractor` — deterministic clustering for feedback signals, with the LLM only naming the clusters.

## Developing Cairn itself

`src/cairn_cli/templates/skills/` is the only committed copy of the skills, and it's what `cairn init` installs. This repo's own `.claude/skills/` is git-ignored and installed from the templates, the same way a user's is. `--skills-only` skips the product skeleton, which this repo doesn't need:

```bash
pip install -e .
cairn init --here --force --skills-only   # refresh .claude/skills/ after editing a template
```

Edit skills under `src/cairn_cli/templates/skills/`, never under `.claude/skills/`, or the next `--force` will overwrite your change.

See the docs above for the full design behind all of this, including the compile-check rule table (C01–C22) and the install/update/packaging model.
