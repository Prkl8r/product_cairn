# Cairn

*Threading the needle: just-in-time requirements, from signal to Spec.*

Cairn is a Markdown-and-YAML workflow for turning raw product signal (feedback, requirement docs, mandates, ideas, analytics) into an engineering-ready Spec, without the LLM hallucinating claims no one can check. A cairn is a trail marker — it shows the way without walking it for you. The PM drives, the agent drafts and critiques, and nothing runs unless the PM asks for it.

**Flow: Signals → Threads → Specs.** One or more signals feed a Thread. The PM creates a Thread from one or more signals, and it moves through three stages of rising fidelity (Exploring, Framing, Validating) until it hands off one or more Specs that engineering (or a coding agent) picks up.

---

## Core concepts

| Term | What it is |
|---|---|
| **Signal** | An artifact, never a stage: raw input that feeds a Thread: `feedback` (tickets, Slack), `requirement` (a doc from another team), `mandate` (a compliance/exec directive), `idea`, or `analytics` (a dated snapshot of a product metric: the number, period, sample size, comparison and the query behind it, never just a dashboard link). Lives at `signals/<type>/<id>.md`. |
| **Thread** | The unit of work. Begins when the PM decides one or more signals are worth pursuing; links to them in `inbound_refs` (signals aren't consumed, so one can feed several Threads) and to what it produced in `outbound_refs`. Has a `stage` (how far the thinking has got) and a `status` (whether it's being worked on). Lives at `threads/<id>.md`. Required frontmatter is only `thread_id`, `stage`, `status`, `owner` — a Thread can be one signal and a paragraph. |
| **Spec** | What a Thread hands off when it leaves Validating — from then on, the artifact engineering works from. Listed in the Thread's `outbound_refs`. One Thread can produce more than one Spec: split Specs when the parts ship separately, and split Threads only when the parts need separate decisions (one could be parked or rejected alone, or has a different sponsor). The scope check in `shape-thread`, `assess-thread` and `draft-spec` asks which, defaulting to one Thread with several Specs. Lives at `specs/<id>.md`. |
| **Charter** (`charter.yaml`) | The product's root boundaries: modality, UI presence, profile (`solo`/`team`), write authority, data classification, org rules. Constrains a Thread; never starts one. |
| **Architecture overview** (`architecture/<system>/overview.md`) | What a system owns, its interfaces, dependencies, constraints, known quirks. Readiness: **L0** uncharted, **L1** drafted/imported, **L2** verified by a named owner. A Spec can rest on L1: it still passes, but carries a warning that engineering must verify those constraints during estimation, and `cairn handoff` writes that warning into the Spec engineering receives. Loaded into context only when a Thread's `touches` names that system. |
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
| **Exploring** | The PM, alone, fleshing out an idea. | Feedback: recurring theme met. Requirement/mandate/idea: a named sponsor validated it. Analytics: the number has a comparison and a known sample size. Problem-and-impact brief written (evidence, alternatives, why now, expected outcome); PM decides **proceed**. | `shape-thread` |
| **Framing** | Talking to others to find what needs thinking about. The jury runs here. | Jury verdict recorded; every edge case mapped to a criterion or deferred. | `assess-thread` |
| **Validating** | Getting everyone on board; UX mocks, an API spec (OpenAPI 3.1) and other supporting artifacts get made. | The Spec compiles clean. No sign-off is required: Cairn reminds the PM who should review the draft (the sponsor, owners of systems in `touches`), and never blocks on it. | `draft-spec` → `check-spec` |

Leaving Validating takes two steps. Once the Spec compiles clean, the PM marks it ready; when it goes out, it's handed off.

**One Thread, several Specs.** When a Thread plans more than one Spec (the `## Planned Specs` table from the scope check), each Spec moves on its own and the Thread's status follows them:

| | Spec (`spec_status` in the Spec) | Thread (`status`) |
|---|---|---|
| Drafting | `drafted` | Active |
| Compiles clean, PM marks it ready | `specified` | stays Active while any other planned Spec isn't ready |
| `cairn handoff` sends it | `handed_off` | stays Active; becomes **Handed off** when the last planned Spec goes out |
| Engineering sends it back | back to `drafted` | Active |

So you can hand off the first Spec as soon as it's ready and keep drafting the rest, with no stepping the Thread back. The Thread is **Specified** only when every planned Spec is ready or out. A Thread with a single Spec can skip `spec_status`: the PM sets the Thread to Specified, and `cairn handoff` sets it to Handed off.

**Status** is separate from stage, so a Thread keeps its stage when it stops:

| Status | Meaning | Skill |
|---|---|---|
| **Active** | Being worked on (default). | — |
| **Parked** | On hold, with what has to happen first (`pickup_when`). | `park-or-reject` |
| **Rejected** | Dropped, with a reason and category. | `park-or-reject` |
| **Specified** | Every planned Spec compiles clean and is ready; at least one hasn't been sent yet. | PM, after a passing `check-spec` |
| **Handed off** | Every planned Spec went out: exported to a team, sent to another repo, or left in place for spec-kit. | `cairn handoff`, when the last Spec goes |

- **Kickback**: engineering sends a Spec back. That Spec returns to `drafted` and the Thread to Active at Validating, while the Thread's other Specs keep their status; `record-kickback` → `revise-spec` updates the same Spec.
- **Fast track**: `fast-track` goes from Exploring to a drafted Spec, backfilling Framing and Validating lightly (`light_stages`), with a Review Brief and one acknowledgement.
- **Handoff** ends Cairn's part: `cairn handoff` exports the Spec to a team, sends it to another repo, or leaves it in place for spec-kit to pick up, and records each Spec sent in the Thread's `handoffs` list. Whoever receives it tracks build and launch.

---

## Getting started

**0. Install Cairn into your product repo.**

```
pip install -e /path/to/product_cairn   # or: pip install -e . from inside this repo
cd /path/to/your-product-repo
cairn init --here                       # or: cairn init <new-project-name>
```

This copies the `.claude/skills/` into the target repo, creates the `signals/`, `threads/`, `specs/`, `journeys/`, `architecture/`, `library/` skeleton, writes a `charter.yaml` template, and pins the installed version in `.cairn/package.lock`. It's idempotent — rerunning `cairn init` never overwrites `charter.yaml` or anything you've already written; pass `--force` to refresh the skill files themselves after an update. Run `cairn doctor` any time to check the install is complete.

**Or install the skills as a Claude Code plugin.** They then show up namespaced as `/cairn:<skill>` (for example `/cairn:whats-next`) in every repo, with no copies to keep in sync:

```
/plugin marketplace add /path/to/product_cairn   # or the GitHub repo
/plugin install cairn@cairn
```

You still need `cairn init` for the `signals/`, `threads/`, `specs/` skeleton and `charter.yaml`. `cairn init` also copies the skills into `.claude/skills/`, so a repo using the plugin shows each skill twice (`/shape-thread` and `/cairn:shape-thread`). Delete the copied ones if you use the plugin.

**Installing for other agents.** Run `cairn init` in a terminal and it asks which agents to install skills for. Use the arrow keys to move, space to tick or untick, and enter to confirm. Agents already in `.cairn/package.lock` start ticked. Every agent gets the same `SKILL.md` folders:

| `--agent` | Tool | Skills folder |
|---|---|---|
| `claude` | Claude Code | `.claude/skills/` |
| `vscode` | VS Code / Copilot agent mode (works with Ollama models picked there) | `.github/skills/` |
| `codex` | OpenAI Codex CLI | `.agents/skills/` |
| `cursor` | Cursor | `.cursor/skills/` |
| `cline` | Cline | `.cline/skills/` |

Scripts and CI skip the menu by passing `--agent`, as many times as needed (`cairn init --here --agent claude --agent vscode`). Without a terminal and without `--agent`, it installs for `claude`. `.cairn/package.lock` records every agent installed, and `cairn doctor` checks each one's folder. Cursor also reads `.agents/skills/`, so a repo with both `codex` and `cursor` shows each skill twice in Cursor.

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

When a Spec is ready (`spec_status: specified`, or a Specified Thread for a single Spec), hand it off:

```bash
cairn handoff SPEC-001 --to export --where "platform team"   # zip a package for a team
cairn handoff SPEC-001 --to repo --where ../other-repo        # copy into another repo's specs/SPEC-001/
cairn handoff SPEC-001 --to in_place                          # leave it here for spec-kit
```

It refuses unless the Spec is ready and its compile report says `## Verdict: Pass`. On a Thread with several Specs, the Thread may still be Active. It then builds `.cairn/handoff/<spec-id>/`: the Spec with a `source` link back to this repo and Thread, plus an `addendum/` holding copies of every supporting artifact in the Thread's `outbound_refs`. Files in the repo are copied, downloadable URLs are fetched, and anything else is listed in `addendum/LINKS.md`. API specs that aren't OpenAPI 3.1 get a warning. Delivery is done by `.cairn/handoff.py`, a script `cairn init` installs once and never overwrites, so each team can change how export and repo work. If it succeeds, the Spec becomes `handed_off` and the handoff is added to the Thread's `handoffs`. The Thread becomes Handed off once all its planned Specs have gone; until then the command says which are still to go. `--dry-run` builds the package and stops.

`--json` and `snapshot` leave out anything marked `data_class: restricted`, including the ids of restricted signals, unless you pass `--include-restricted`. Plain terminal output shows everything and tags restricted items. Every output lists broken references (a Thread or Spec pointing at a signal, Thread, or library file that doesn't exist), and `cairn doctor` warns about them.

**1. Onboard the product, once.** Nothing else works without a ratified `charter.yaml` and at least an L1 overview for the systems a Thread will touch:

```
onboard            # brownfield: pulls from the codebase and/or a connected tracker
onboard --new      # greenfield: runs an interview instead
```

**2. Capture a signal.** Run `intake-signal` with the quote, ticket, directive or metric. It writes `signals/<type>/<id>.md` (redacted/committed) with a raw copy under `signals/<type>/raw/` (git-ignored).

**3. Start a Thread.** Minimal frontmatter — `thread_id`, `stage: Exploring`, `status: Active`, `owner`, `inbound_refs`, `touches` — plus one paragraph of what this is and why it matters. If it grows to cover several parts that could ship separately, the scope check adds a `## Planned Specs` table (and matching `planned_specs` frontmatter) showing how it will split into Specs and in what order.

**4. Move it.** Either walk the core flow (below) or say "take this to Spec" for `fast-track`.

**5. Lost?** Run `whats-next` on any Thread — it reads the stage and status and tells you, in plain language, which skill to run next.

---

## The core flow

Four skills, run in order, cover the normal track end to end:

1. **`shape-thread`** — Exploring → Framing (or Parked/Rejected). Checks the entry gate, drafts a problem-and-impact brief that asks whether the problem is worth solving (evidence strength, alternatives, why now, expected outcome), gets the PM's proceed/hold/drop call.
2. **`assess-thread`** — The Framing-stage critique, then Framing → Validating. Runs the Advocate/Skeptic/Judge jury, maps every edge case to a future criterion or a deferral, records the verdict.
3. **`draft-spec`** — Drafts the Spec from a Validating Thread's jury verdict: binary-or-thresholded criteria, each traced to a real source, grouped into verifiable slices.
4. **`check-spec`** — The deterministic gate. Checks structure, traceability, criteria quality, slices, and that no open question is left hanging — by hand, standing in for the `mcp-spec-compiler` server that doesn't exist yet. No LLM judgment calls on correctness, only well-formedness. Afterwards it offers to walk through any open warnings, up to three at a time: acknowledge each (it records an `ack` line with the reason), edit the Spec to clear it, or leave it open. C24 warnings about unverified architecture can't be acknowledged.

**The loop-back**, for when engineering sends a Spec back: **`record-kickback`** logs why and sets the Thread's status back to Active (it stays in Validating); **`revise-spec`** redrafts only the affected slices under the *same* `spec_id` at a bumped `revision`, so it reads as an update, not a new document.

**The shortcut**: **`fast-track`** jumps straight from Exploring to a drafted Spec, backfilling Framing and Validating in light form (a short brief, a single-pass critique instead of the full jury) and writing a **Review Brief** — verify-first items, every assumption tagged by origin (`signal`/`overview`/`library`/`inferred`), open questions, and what was skipped. One acknowledgement (`brief_ack`) is the only checkpoint; `check-spec` still enforces everything else.

**The jury**: **`jury-duty`** runs the Advocate/Skeptic/Judge critique that `assess-thread` calls, and a PM can run it alone to pressure-test anything. In Claude Code each seat is its own agent (`jury-advocate`, `jury-skeptic`, `jury-judge`). The Judge runs on Opus, and before each jury `cairn jury-draw` flips a coin to decide whether the Advocate or the Skeptic gets Opus, the other getting Sonnet. That way the stronger model doesn't always argue for the proposal, and the Judge shares a model with each side equally often. The draw is recorded in the verdict. Each juror returns a short, fixed-format result, so the debate doesn't flood the conversation. Other agents play the three seats inline, and the verdict records `jury_mode: inline` so you know the Skeptic shared a model. Pin a seat's model under `jury.models` in `.cairn/config.yaml`, or set `jury.draw: fixed` to turn the coin flip off.

**The interview**: **`ask-me`** fills in a Thread by asking the PM three questions at a time, multiple choice or free form, aimed at whatever its stage is missing: problem and evidence in Exploring, use cases in Framing, acceptance criteria, thresholds and error states in Validating. Answers go in the Thread's `## Q&A` (`qa-01`, `qa-02`, …) and into `use_cases` and `candidate_criteria`, so `draft-spec` can trace criteria to the PM's own decisions (`basis: decided`). Run it any time; it never moves the Thread on.

**The journey**: **`map-journey`** maps the user journey a Thread changes, step by step: the user's goal, what they do, what the system does, and the error and empty cases. Each step is traced to a signal or overview or tagged `inferred`. Run it in Framing so the jury attacks concrete steps, or in Validating so the Spec can trace criteria to steps (`journey:JRN-001#step-2`). It's written to `journeys/<id>.md`, linked in `outbound_refs`, and copied into the handoff package. `check-spec` C26 warns about steps no criterion covers.

**Housekeeping**: **`bundle-threads`** ties related Threads together (same problem, a duplicate, or work that should ship together) so they show as one group in the ledger and in lookups; it never merges them or changes their stage. **`park-or-reject`** parks, resumes or rejects a Thread at any stage.

**The navigator**: **`whats-next`** is a lookup, not a gate. Point it at a Thread (or nothing, for the most recently touched one) and it names the one thing to do next — so nobody has to memorize this table.

**The prerequisite**: **`onboard`** is the one entry point before any Thread can exist. Brownfield, it pulls context itself — scanning a codebase (READMEs, manifests, directory layout, OpenAPI/schema files, infra config) and/or querying a connected tracker (Jira, Linear, ClickUp, Monday, Asana) — rather than waiting for the PM to hand it docs. Greenfield (`--new`), it runs a structured interview and leaves unanswered fields as visible `TBD`. Either way it never self-verifies: every overview it produces starts at L1, and only a named human can promote one to L2.

Everything an agent drafts is marked agent-drafted until the PM edits or accepts it. Nothing above changes a Thread's stage or status or writes a file without the PM asking.

---

## Repo layout

```
charter.yaml                     # product root boundaries (from onboard)
.cairn/handoff.py                # your delivery script for cairn handoff (yours to edit)
.cairn/config.yaml               # project settings, e.g. jury models (yours to edit)
.cairn/handoff/<spec-id>/        # built handoff packages (git-ignored)
signals/<type>/<id>.md           # committed, redacted signal
signals/<type>/raw/<id>.*        # git-ignored raw copy
threads/<id>.md                  # one Thread per unit of work
specs/<id>.md                    # compiled output, one or more per Thread
specs/<id>.compile_report.md     # check-spec's output for that Spec
journeys/<id>.md                 # user journeys from map-journey (optional)
architecture/<system>/overview.md  # one per system a Thread can `touches`
library/                         # historical specs, compliance docs (optional)
.claude/skills/                  # the skills documented above
.claude/agents/jury-*.md         # the jury's three seats (Claude Code only)
docs/
  spec-as-code-master-document.md  # the PRD: outcomes, behavior, metrics
  spec-as-code-revision.md         # full lifecycle, check-spec rules, install/update design
```

---

## Roadmap: what's not built yet

The core flow above is complete. Still missing, named today only as placeholders in `whats-next`'s own dispatch table:

- **`onboard`'s onboarding is done**; the rest below are genuinely optional, built when a PM first asks for them:
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

**Bump the version with every push.** Claude Code only picks up a plugin update when `version` changes, so an unbumped push leaves plugin users on the old skills. The version lives in three places that must match: `pyproject.toml`, `src/cairn_cli/__init__.py` and `src/cairn_cli/templates/.claude-plugin/plugin.json`. `tests/test_version.py` fails if they drift. Use a minor bump (0.2.0 → 0.3.0) for skill or behavior changes and a patch bump for fixes and doc-only changes.

Run the tests with `pip install pytest && pytest tests`.

See the docs above for the full design behind all of this, including the check-spec rule table (C01–C26) and the install/update/packaging model.
