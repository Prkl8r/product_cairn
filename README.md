# Cairn

*Threading the needle: just-in-time requirements, from signal to Spec.*

Cairn is a Markdown-and-YAML workflow for turning raw product signal (feedback, requirement docs, mandates, ideas) into an engineering-ready Spec, without the LLM hallucinating claims no one can check. A cairn is a trail marker — it shows the way without walking it for you. The PM drives, the agent drafts and critiques, and nothing runs unless the PM asks for it.

**Flow: Signals → Threads → Specs.** One or more signals feed a Thread. A Thread is pulled through progressive gates until it compiles into one or more Specs that engineering (or a coding agent) picks up.

---

## Core concepts

| Term | What it is |
|---|---|
| **Signal** | Raw input that starts or feeds a Thread: `feedback` (tickets, Slack), `requirement` (a doc from another team), `mandate` (a compliance/exec directive), or `idea`. Lives at `signals/<type>/<id>.md`. |
| **Thread** | The unit of work. Begins when a signal is captured, carries lineage (`inbound_refs`/`outbound_refs`), and moves through the gates below. Lives at `threads/<id>.md`. Required frontmatter is only `thread_id`, `state`, `owner` — a Thread can be one signal and a paragraph. |
| **Spec** | The compiled output of a Thread at Contract — what engineering picks up. One Thread can produce more than one Spec. Lives at `specs/<id>.md`. |
| **Charter** (`charter.yaml`) | The product's root boundaries: modality, UI presence, profile (`solo`/`team`), write authority, data classification, org rules. Constrains a Thread; never starts one. |
| **Architecture overview** (`architecture/<system>/overview.md`) | What a system owns, its interfaces, dependencies, constraints, known quirks. Readiness: **L0** uncharted, **L1** drafted/imported, **L2** verified by a named owner. Loaded into context only when a Thread's `touches` names that system. |
| **Track** | `normal` (every gate, full jury) or `fast` (skip Shape/Feasibility, backfill them lightly, write a Review Brief). Either way the compile check's traceability rules still apply. |

Gates are guardrails, not a prison. The PM can skip ahead (`fast-track`) or step around a check; the system never silently blocks, it tells you what you're skipping and what to verify.

---

## The lifecycle

```
Signal ──► Shape ──► Feasibility ──► Contract ──► Launched
  │           │            │             │
  │           ▼            ▼             ▼
  └──────► Parked / Rejected      (eng kickback)
                                         │
                                         ▼
                                   back to Feasibility
                                   (record-kickback → revise-spec)

Fast track: Signal ──────────────────► Contract
            (Shape + Feasibility backfilled, Review Brief, one ack)
```

| Gate | Checkable condition | Skill that drives it |
|---|---|---|
| Signal → Shape | Feedback: recurring theme met. Requirement/mandate/idea: a named sponsor validated it. | `shape-thread` |
| Shape → Feasibility | PM decides **proceed** / **hold** (Parked) / **drop** (Rejected). Every system in `touches` has an overview (warn on `solo`). | `shape-thread` |
| Feasibility → Contract | Jury verdict present; every edge case mapped to a criterion or deferred. | `assess-thread` → `spec-generator` |
| Contract → Launched | Spec compiles clean; eng accepted; enablement linked; overviews updated or attested unchanged. | *not yet built — see Roadmap* |
| Contract → Feasibility | Engineering kickback. | `record-kickback` → `revise-spec` |
| Any → Contract (fast track) | PM invokes `fast-track`; Review Brief acknowledged; compiler errors cleared. | `fast-track` |
| Any → Parked / Rejected | PM's call, with a reason (and a revisit date for Parked). | `shape-thread` |

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
cairn ledger              # every signal (and whether a Thread picked it up), Threads by state, Specs sent to engineering
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

**3. Start a Thread.** Minimal frontmatter — `thread_id`, `state: Signal`, `owner`, `inbound_refs`, `touches` — plus one paragraph of what this is and why it matters.

**4. Move it.** Either walk the core spine (below) or say "take this to Spec" for `fast-track`.

**5. Lost?** Run `whats-next` on any Thread — it reads the state and tells you, in plain language, which skill to run next.

---

## The core spine

Four skills, run in order, cover the normal track end to end:

1. **`shape-thread`** — Signal → Shape → Feasibility (or stops at Parked/Rejected). Checks the entry gate, drafts a problem-and-impact brief, gets the PM's proceed/hold/drop call.
2. **`assess-thread`** — The Feasibility-stage critique. Runs the Advocate/Skeptic/Judge jury, maps every edge case to a future criterion or a deferral, records the verdict.
3. **`spec-generator`** — Drafts the Contract-level Spec from a Feasibility Thread's jury verdict: binary-or-thresholded criteria, each traced to a real source, grouped into verifiable slices.
4. **`compile-check`** — The deterministic gate. Checks structure, traceability, criteria quality, slices, and that no open question is left hanging — by hand, standing in for the `mcp-spec-compiler` server that doesn't exist yet. No LLM judgment calls on correctness, only well-formedness.

**The loop-back**, for when engineering sends a Spec back: **`record-kickback`** logs why and moves the Thread back to Feasibility; **`revise-spec`** redrafts only the affected slices under the *same* `spec_id` at a bumped `revision`, so it reads as an update, not a new document.

**The shortcut**: **`fast-track`** jumps straight from Signal to a drafted Spec, backfilling Shape and Feasibility in light form (a short brief, a single-pass critique instead of the full jury) and writing a **Review Brief** — verify-first items, every assumption tagged by origin (`signal`/`overview`/`library`/`inferred`), open questions, and what was skipped. One acknowledgement (`brief_ack`) is the only checkpoint; `compile-check` still enforces everything else.

**The navigator**: **`whats-next`** is a lookup, not a gate. Point it at a Thread (or nothing, for the most recently touched one) and it names the one thing to do next — so nobody has to memorize this table.

**The prerequisite**: **`onboard-product`** is the one entry point before any Thread can exist. Brownfield, it pulls context itself — scanning a codebase (READMEs, manifests, directory layout, OpenAPI/schema files, infra config) and/or querying a connected tracker (Jira, Linear, ClickUp, Monday, Asana) — rather than waiting for the PM to hand it docs. Greenfield (`--new`), it runs a structured interview and leaves unanswered fields as visible `TBD`. Either way it never self-verifies: every overview it produces starts at L1, and only a named human can promote one to L2.

Everything an agent drafts is marked agent-drafted until the PM edits or accepts it. Nothing above changes a Thread's state or writes a file without the PM asking.

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

The core spine above is complete. Still missing, named today only as placeholders in `whats-next`'s own dispatch table:

- **A Launched-gate skill** — nothing currently packages the enablement artifact or checks the overview-attestation before `Contract → Launched`.
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
