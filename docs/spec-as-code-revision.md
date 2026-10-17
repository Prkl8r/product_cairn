# Cairn: Revised PRD Outline and Compile-Step Validator Spec

**Product:** *Cairn: The Context-Aware "Spec-as-Code" Workflow Guide*

*Threading the needle: just-in-time requirements, from signal to Spec.*

## Part 1: Revised PRD Outline

Goal of the restructure: keep the PRD about outcomes and behavior. Move implementation detail and checklists to appendices.

### Terminology
**Flow: Signals -> Threads -> Specs.** Signals are captured, one or more of them feed a Thread, and each Thread is pulled through the gates until it compiles into one or more Specs that engineering picks up.

- **Signal:** any raw input that feeds a Thread. A signal is an artifact, never a stage. Signal types:
  - **feedback**: customer requests, support tickets, Slack threads
  - **requirement**: a requirement doc from a business team or upstream group
  - **mandate**: a corporate, executive, or compliance directive
  - **idea**: an internal idea or proposal, including a shower thought
- **Cairn (the product):** the name of the tool. A cairn is a trail marker that shows the way without walking it for you. Signals, Threads, and Specs are what it works with.
- **Thread:** the unit of work. It begins when a signal is captured, carries lineage in `inbound_refs` and `outbound_refs`, and is pulled through the gates.
- **Stages and status:** a Thread has a `stage` (Exploring, Framing, Validating: how far the thinking has got) and a separate `status` (Active, Parked, Rejected, Specified, Handed off: whether it is being worked on). A Thread is created when the PM decides one or more signals are worth pursuing.
- **Spec:** what a Thread hands off when it leaves Validating. This is what engineering picks up. One Thread produces one or more Specs.
- **Context, not signals:** the charter (`charter.yaml`, the product's root boundaries, called the constitution in the original PRD), architecture overviews, and library. They constrain a Thread but never start one.
- **Ref format:** typed prefix plus ID, for example `feedback:ZD-88421`, `req:REQ-SEC-2026-A`, `mandate:MANDATE-Q3`, `idea:IDEA-017`. All signal refs resolve under `/signals/<type>/`.

### 1. Problem and Outcomes
- Problem: specs are written from unstructured signals (feedback, requirement docs, mandates, ideas), so LLM drafts contain claims no one can trace.
- Reframed outcome: **every claim in a handed-off Spec is traceable to a signal or library reference, and unsupported claims fail compilation.** (Replaces "zero hallucination.")
- Secondary outcomes: local-first tracking, tool-agnostic execution via MCP, enablement planned before build.
- Non-goals: replacing engineering review, replacing Jira for engineering execution, autonomous spec approval.

### 2. Users and Roles
- PM (author), approver (anyone the PM chooses to ask, if anyone), engineering reviewer, GTM/enablement consumer, signal sources (support, business teams, leadership).
- For each role: what they touch, and where (repo, read-only view, or external tool).
- Decision needed: how non-git users read Threads and Specs (rendered read-only site, export, or sync).

### 3. Design Principles
1. Deterministic tools own rules, state, and validation. LLMs own drafting and critique.
2. Every generated claim carries provenance.
3. Checks are machine-checkable. Approvals are facts the PM records, not permissions the tool grants.
4. Default to local execution and minimal data in git.
5. Gates are guardrails, not a prison. The PM can skip stages. The system does the missing work and flags what to review (see Fast Track in section 4).
6. A guide, not a factory. The PM drives, the agent advises, and nothing runs unless the PM asks.
7. Clear before it ships. A Spec that is handed off has no open questions. Each one is answered, deferred with a reason and an owner, or moved to out of scope. There is no separate clarification step: the agent asks early ("ask before assuming"), and the compile step confirms nothing was left open.

#### Guide, not a factory
The system helps the PM think, shape, and check. It does not mass-produce Specs, and it is not a pipeline the PM feeds. If a feature makes the PM feel like an operator on an assembly line, that feature is wrong.

- **The PM drives.** No stage advances, no Spec is generated, and nothing syncs to an external tracker unless the PM asks. Automation (auto-sync, auto-commit) is opt-in, one behavior at a time, and never the default.
- **Ask before assuming.** At each stage the agent's default move is a short, targeted question or a suggestion with a recommended option, not a finished artifact. It asks only the questions whose answers would change the Spec.
- **Help on demand, at any stage.** The PM can ask at any time: "what am I missing?", "what would engineering ask?", "argue against this", "find similar past Threads", "tighten these criteria", "is this ready for engineering?", "draft the ask to Sarah." These are moves in a conversation, not stages.
- **Agent text is labeled.** Anything the agent writes is marked agent-drafted until the PM edits or accepts it, so the PM can always see what is theirs and what is not.
- **Advice can be ignored.** Caution flags, next-step suggestions, and missing-overview notes are advice. The only things that can fail are checks the PM turned on and the compiler's well-formedness checks on a Spec headed to engineering.
- **Minimal by default.** A Thread's required frontmatter is `thread_id`, `stage`, `status`, and `owner`. Everything else is added when it is useful. A Thread can be a single signal and a paragraph.
- **No throughput targets.** Nothing measures Specs per week or compares PMs. Metrics are diagnostics for the PM (see section 11).
- **Language.** The original PRD calls this an "engine" and talks about "compiling." The product is called Cairn. It is a guide and not an engine, and "compile" is reserved for the narrow Spec well-formedness check.

### 4. Thread Lifecycle
Stages: **Exploring**, **Framing**, **Validating**. Each name says what is happening now; each gate is what must be true to leave it. Status is a separate field, so a Thread keeps its stage when it stops.

| Stage | What's happening | Exit gate (checkable) | Required fields |
|---|---|---|---|
| Exploring | The PM, alone, fleshing out an idea | Feedback: recurring-theme threshold met. Requirement, mandate, or idea: a named sponsor has validated it. Problem-and-impact brief written (problem, evidence and its strength, alternatives, why now, expected outcome); PM decides **proceed** | `inbound_refs`, `validated_by` (plus `themes` for feedback), `evidence_strength` |
| Framing | Talking to others to find what needs thinking about; the jury runs here | Every system in `touches` has an overview (warning on the `solo` profile). Jury verdict present, all edge cases mapped or deferred | `touches`, `verdict_ref` |
| Validating | Getting everyone on board; UX mocks, an API spec (OpenAPI 3.1) and other supporting artifacts get made | The Spec compiles clean. No sign-off required: Cairn reminds the PM who should review (the sponsor, owners of systems in `touches`) and never blocks on it | `compile_report`, `outbound_refs` |

| Status | Meaning | Required fields |
|---|---|---|
| Active | Being worked on (default) | — |
| Parked | On hold, keeps its stage | `reason`, `pickup_when` |
| Rejected | Dropped, keeps its stage | `reason`, `reject_category` |
| Specified | The Spec compiles clean; not sent anywhere yet. Set by the PM | `compile_report` |
| Handed off | The Spec went out (export, another repo, or in place for spec-kit). Set by `cairn handoff` | `handoff` |

Transitions outside the normal order:

| Move | Gate | Required fields |
|---|---|---|
| Kickback: Handed off → Active, stage stays Validating | Engineering sends the Spec back | `kickback_reason`, `kickback_category` |
| Fast track: Exploring → a drafted Spec at Validating | PM invokes `fast-track`; Review Brief acknowledged; compiler errors cleared | `track: fast`, `light_stages`, `brief_ack` |

Handoff ends Cairn's part. Whoever receives the Spec tracks build and launch.

Kickback categories (feed the kickback-rate metric): missing edge case, ambiguous criterion, wrong constraint, scope change.

**Proceed decision.** When a Thread leaves Exploring, the PM (with the agent's help on research, a crisp problem definition, and a short case for and against) lands on one of three outcomes: **proceed** (move to Framing), **hold** (Parked, with the open questions and a revisit date), or **drop** (Rejected, with the reason). The reason is searchable later, so a dropped idea is not re-argued from scratch.

#### Fast Track (gates are guardrails, not a prison)
The PM owns the Thread and can jump from Exploring straight to a Spec when the work is small, low risk, or already well understood. The system never blocks the jump. It does the missing work and tells the PM where to look.

**How it works**
1. The PM runs `fast-track THRD-042` (or says "take this to Spec") from any stage. The agent may suggest it for a small Thread but never starts it on its own.
2. The agent backfills each skipped stage in lightweight form:
   - Exploring: a short problem and impact brief drafted from the signal.
   - Framing: a single-pass critique with the top edge cases and risks, each mapped to a criterion or a deferral. No three-round debate.
   - Validating: the Spec draft, compiled as usual. No supporting artifacts are made; the review reminder still goes in `## Open items`.
   - Overviews: a list of touched systems, noting any overview that is missing or unverified.
3. The agent writes a **Review Brief** at the top of the Thread. It is short and ranked:
   - **Verify first:** the 3 to 5 items most likely to be wrong or most costly if wrong.
   - **Assumptions:** every assumption the agent made, each tagged with its origin (`signal`, `overview`, `library`, or `inferred`).
   - **Open questions** the agent could not resolve.
   - **Skipped:** which gates were bypassed and what was drafted in their place.
   - **Caution flag (optional):** if the work looks risky for a fast track (touches an unverified system, changes a public API, rests mostly on inferred assumptions), the agent says so plainly. It still proceeds. The call is the PM's.
4. The PM acknowledges the Brief with one action (`ack-brief`). That single acknowledgement is the only checkpoint.
5. The Thread records what happened, as transparency rather than punishment:

```yaml
track: fast
light_stages: [Framing, Validating]
skipped_gates: [Framing, Validating]
review_brief:
  verify_first:
    - "AC-003 sets a 300 ms p95 target. Source is the mandate, no load data seen."
  assumptions:
    - id: A1
      text: "Rate limit applies per API key, not per IP."
      origin: inferred        # signal | overview | library | inferred
  open_questions: ["Does the limit apply to internal callers?"]
brief_ack: <commit>
```

**What fast track does not waive.** The compiler still enforces traceability, schema, modality, binary-criteria lint, and required sections (use `n/a: <reason>` for sections that do not apply to a small change). These protect engineering from a bad Spec and cost the PM almost nothing when the agent drafts correctly.

**What relaxes.** The full jury debate and overview coverage become backfilled drafts or warnings (details in Part 2). Approvals were never required, so there is nothing to waive there.

**Org rules (optional, off by default).** If the PM's organization requires someone else to sign off on certain things, for example `restricted` data, compliance or InfoSec mandates, or changes to a public API contract, the charter can list them. By default the agent only reminds the PM ("this one usually needs a sign-off, want me to draft the ask?") and carries on. Setting `enforcement: block` makes it a hard stop, and should only be used when the org truly requires it.

**Calibration, not policing.** Metrics are segmented by track, so the PM can see whether fast-tracked Specs get kicked back more often. That data lives in the repo and is for the PM's own tuning first. Who else sees it is a reporting choice, not a built-in feature.

#### Approvals (recorded, not enforced)
Approvals are facts the PM records, not permissions the tool grants. The system never asks "who approved this?" before a Thread moves. If you need someone's OK, you get it the way you normally would (a meeting, a Slack reply, a hallway conversation) and, if you want it on record, you tell the agent.

- **Record it.** "Sarah OK'd the shape in Slack." The agent adds an entry to the Thread: `approvals: [{by, how, date, link, note}]`. Link and note are optional.
- **Ask for it.** "Draft the ask to Sarah." The agent writes the message from the Thread (problem, impact, decision needed, what you would do by default). You send it however you like. The Thread shows the ask as pending until you record the reply.
- **Suggestions, not stops.** The agent may say "mandates like this usually need a sponsor's OK, want me to draft the ask?" and then move on. If `charter.yaml` lists `approver_suggestions`, the agent uses them to name who to ask.
- **Self-imposed blocks.** If you mark an approval `blocking: true` on a Thread, the tracker holds that Thread's transitions until the approval is recorded as granted. You set the rule, so you can lift it.
- **Skipping approvals is normal.** A Thread with no approvals simply has none on record. That is a fact, not a violation.

#### Profiles: `solo` and `team`
`charter.yaml` sets `profile`. Cairn is the same and only the defaults change, so the same setup works for a work product or a personal project.

| Behavior | `solo` | `team` |
|---|---|---|
| Approvals | Off, never suggested | Recorded when the PM wants them, suggested for mandates |
| External sync | Off | On if configured |
| Enablement and GTM checks | Off (`enablement_deps` may be `n/a`) | On |
| Overview coverage (C17) | Warn | Error |
| Review Brief acknowledgement (C18) | Warn | Error |
| Org rules (C19) | None | Warn by default, Error only if `enforcement: block` |
| Who reads the Spec | You or a coding agent | The engineering team |

For personal projects the Spec still earns its place: it is the written contract you or a coding agent builds against, with the same traceability and binary-criteria checks.

### 5. Context Model
- `charter.yaml`: modality, UI presence, profile (`solo` or `team`), write authority, data classification defaults, optional approver suggestions and org rules, version.
- `/architecture/` and `/library/`: loaded via explicit `touches: [system-a, system-b]` tags in Thread frontmatter. Add semantic search only if the library outgrows tag routing.
- Versioning: charter, skills, and prompts carry versions, recorded in every compiled Spec.

### 6. Product Onboarding (Brownfield and New Product)
One entry point, `onboard-product`, with two paths. Both end in the same state: a ratified `charter.yaml` and product overviews at a known readiness level. No Thread can be created until both exist.

**Readiness levels (per system)**
- L0: uncharted, nothing documented.
- L1: drafted or imported, not verified.
- L2: verified by a named owner and inside its review window (`review_ttl`).

**Path A: Brownfield (existing product)**
1. **Charter first.** An import skill reads existing docs and proposes `charter.yaml` (modality, UI presence, profile). The PM ratifies it by hand.
2. **Import into `/library` and `/architecture` with provenance.** `mcp-brownfield-import` scans old specs, wiki pages, OpenAPI files, and architecture docs. Each file gets frontmatter: `source`, `imported_on`, `owner`, `verified: false`, `last_verified`, `review_ttl`. Where a deterministic source exists (OpenAPI, schemas), generate from it directly. The LLM only summarizes.
3. **Generate product and system overviews** from the imported material, using the overview template in Appendix E. Everything starts at L1.
4. **Bring in only in-flight work.** Convert open Jira epics into Threads at the stage and status that match reality, tagged `legacy: true`, with the Jira key in `inbound_refs`. Closed history stays in Jira. Legacy Specs get the C04 waiver (see Part 2) and a `legacy_untraced` stamp.
5. **Capture as-built behavior and known debt** in `/architecture/<system>/known-quirks.md`. Undocumented current behavior is the most common cause of brownfield kickbacks.
6. **Backfill lazily.** The first new Thread that lists a system in `touches` triggers a verify task for that system's files. Touch it, verify it. Coverage grows along real work, not through a migration project.
7. **Pilot on one slice**, such as one API or one client, and reach L2 on just those systems first.

**Path B: New product (greenfield)**
1. The PM runs `onboard-product --new`. The `product-overview-interview` skill asks for: purpose, target users, modality, boundaries, key systems, interfaces, dependencies, data classes, success targets, non-goals, and owners.
2. Outputs: a draft `charter.yaml`, `/architecture/product-overview.md`, and one overview per planned system, all using the Appendix E template.
3. There is no source to import from, so the interview answers are the source (`source: interview`). The skill must not invent content. Unanswered fields stay `TBD`, and any `TBD` blocks promotion to L2.
4. The PM or architect ratifies each overview to L2 by setting `verified: true` with their name and date.
5. Overviews stay current. A Spec that changes a system's boundaries or interfaces must update that system's overview in the same commit, or attest `overview_unchanged: true` before handoff.

**Rules for both paths**
- Every overview needs a named `owner`. An unowned file can never reach L2.
- Imported or interview-drafted content never counts as verified until a human says so.
- Do not treat old tickets as feedback signals. They are internal artifacts.

### 7. Components (summary only)
- MCP servers: local-tracker, signal-ingest, library-rag, external-sync, **spec-compiler (new)**.
- `signal-ingest` uses one adapter per signal type: feedback (Zendesk, Slack), requirement (doc or wiki import), mandate (document or email upload), idea (quick capture). Every adapter writes a raw copy to `/signals/<type>/raw/` (git-ignored) and a redacted signal file to `/signals/<type>/<id>.md` (committed), with the same frontmatter (`signal_id`, `type`, `source`, `captured_on`, `data_class`).
- Skills: theme-extractor (naming and summarizing only), pm-jury-duty, spec-generator, **fast-track (new)**, which backfills skipped stages and writes the Review Brief.
- Clustering inside theme-extractor is a deterministic step, not an LLM step, and applies to feedback signals. Requirement, mandate, and idea signals do not cluster. They need a structured intake step that extracts problem, sponsor, constraints, and success target (see open questions).

### 8. Trust Model
- Compile step (Part 2) is the enforcement point.
- Readiness check (on demand, advisory): the PM asks "is this ready for engineering?" and the agent reviews the Spec for what the compiler cannot see: ambiguous wording, criteria that contradict each other or the charter, missing scenarios, and anything an engineer would have to guess. The output is a short ranked list. It replaces the static Definition of Ready list, whose deterministic items are now compiler checks.
- Eval harness: golden set of 10 to 20 past Threads with known-good Specs. Runs on any change to a skill, the charter, or the model. Tracks criterion recall, orphan-claim rate, and kickback proxy.
- Jury: Skeptic runs on a different model than Advocate and Judge. Output must be concrete edge cases, each mapped to an acceptance criterion or a deferral.

### 9. Data Handling and Security
- Data classification field on each Thread (`public`, `internal`, `restricted`) drives model routing, not per-skill rules.
- Signals are stored in two forms. The raw copy goes in `/signals/<type>/raw/` and is always git-ignored. The redacted signal file at `/signals/<type>/<id>.md` is committed, so trace refs and quote checks resolve on a fresh clone or in CI. Redaction runs in `signal-ingest` before the committed file is written. For mandates and ideas, the original can be committed directly when the data class allows, with no separate raw copy.
- Credentials via keystore or git-ignored `.env`. Write authority per product in the charter.

### 10. External Sync
- Local to external: when a Thread's Spec is handed off, Cairn can create the Epic and keep it updated. Whether that happens automatically, by suggestion, or not at all is chosen per integration (see Background housekeeping below).
- External to local, one-way, limited fields: `exec_status`, `sprint`, `assignee`. Written to a separate `sync/` file, never into authored frontmatter.
- Conflict rule: authored fields are local-wins, execution fields are external-wins.

#### Background housekeeping (replaces "Invisible Administration")
The original Phase D had the agent create the Epic silently. Revised: housekeeping happens in the background, through suggestions or through choices made once at setup.

- **Setup-time modes.** During `cairn init` (and any time later with `cairn config`), each integration gets a mode: `off`, `suggest`, or `auto`. Defaults: the `solo` profile is `off` for everything external, and the `team` profile is `suggest`. `auto` is always an explicit choice, per integration and per product.
- **Suggest mode.** When something housekeeping-shaped becomes true (a Thread's Spec compiles and is handed off, a Spec changes after its Epic was created, an overview passes its review window, an enablement asset is still missing at launch), Cairn adds a one-line item to the **inbox** (`.cairn/inbox.md`). Example: "THRD-042 was handed off. Create the Jira Epic? [create] [edit first] [not this time] [never for this product]."
- **Quiet delivery.** The inbox never interrupts work. It surfaces at natural pauses: session start, after a commit, or when the PM asks "what's pending?". Stale items expire, and ignoring one costs nothing.
- **Dismissals stick.** "Never for this product" is saved in config, so the same suggestion does not come back.
- **Auto mode.** If the PM opts in, the action runs and is written to the Thread's changelog, with an undo where the target system allows it.
- **One channel.** Changelog entries, status updates, approval follow-ups, stale-overview reminders, enablement reminders, and new package releases all use the same inbox. There is no second notification path.

### 11. Metrics
- Time-to-Spec, paired with kickback rate so speed is not rewarded alone. Segment every metric by signal type and by track (normal or fast). Cycle times differ by type, and comparing kickback rate across tracks shows the PM whether fast track is paying off.
- Orphan-claim rate (from compiler reports), replacing the loose "Context Preservation Ratio."
- Enablement attach rate.
- Outcome metric: shipped feature met its stated success target after N days.
- Capture baselines for the current process before the pilot starts.
- These are diagnostics for the PM, not targets to hit. There is no Specs-per-week measure, and nothing compares PMs.

### 12. Pilot Plan
- One product, one quarter, 5 to 8 Threads.
- Success criteria set up front: kickback rate below baseline, orphan-claim rate under a set threshold, PM time spent on admin down, eng reviewers rate Specs as ready at least as often as today, and the PM says it improved their thinking and not only their speed.
- Exit criteria: what would make you stop or redesign.

### 13. Install, Update, and Packaging
Cairn ships as a versioned package that installs into a product repo and updates without touching the PM's content.

**Two layers, never mixed**
- **Package-owned:** skills, MCP servers, compiler checks and lint lists, schemas, templates, migrations. Replaced on update.
- **User-owned:** `charter.yaml`, signals, Threads, Specs, overviews, library, config, and any overrides. Never overwritten by install or update.

```
cairn-package/                   # the package (versioned, package-owned, installed as `cairn`)
  skills/                     # theme-extractor, pm-jury-duty, spec-generator, fast-track, onboarding
  servers/                    # local-tracker, signal-ingest, library-rag, external-sync, spec-compiler
  addons/                     # optional signal adapters, sync targets, export formats
  checks/                     # compiler rules, lint lists, severity defaults per profile
  schemas/                    # Thread, Spec, Overview frontmatter (with schema_version)
  templates/                  # Thread, Spec, Overview, profile defaults (solo, team)
  migrations/                 # versioned scripts, one per schema change
  CHANGELOG.md

<product repo>/               # after `cairn init` (user-owned, except .cairn/package.lock)
  charter.yaml
  signals/  threads/  specs/  architecture/  library/
  .cairn/
    package.lock              # pinned package version and checksums
    config.yaml               # integration modes, enforcement, dismissals
    overrides/                # the PM's changes to skills, lint terms, checks
    inbox.md                  # background suggestions
```

**Install**
1. Install the package with one command (from an internal registry or a git tag).
2. In a product repo, run `cairn init`. It asks for the profile (`solo` or `team`), creates the skeleton, writes `.cairn/package.lock`, adds `.gitignore` entries (`signals/*/raw/`, `.env`, `.env.*`, `.cairn/inbox.md`, `.cairn/local/`, and local index files), and offers `onboard-product` (brownfield or new). It is idempotent and never overwrites an existing file.
3. MCP servers are registered with the host assistant or IDE by writing a config snippet the PM approves, or by printing it. Nothing is edited silently. Skills are generated from one source into each host's format (host wrappers), alongside a shared instruction file (`AGENTS.md` or the host's equivalent), so every assistant gets the same guidance.
4. `cairn doctor` checks the setup: servers start, credentials resolve, the charter validates, and schemas match the lock.
5. Setup choices (integration modes, org rules, approver suggestions) are asked once, in plain language, with defaults per profile. `cairn config` changes them later.

**Customize without forking**
Changes go in `.cairn/overrides/`: tweaked skill prompts, extra lint terms, custom checks. Overrides layer on top of package defaults. An optional **org layer** (shared defaults a team publishes, such as profile defaults, org rules, and approver suggestions) sits between the package and the PM's overrides.

**Add-ons and starter sets**
- **Add-ons** are optional capabilities installed only when needed: signal adapters (for example `cairn add feedback-zendesk`), external sync targets (Jira, Linear), and export formats (a Jira Epic body, a Word or PDF doc, a folder layout that spec-driven coding tools can read). The core stays small: tracker, compiler, and the core skills.
- **Starter sets** are role-based selections of add-ons and defaults (for example PM, enablement, solo builder), so a new user installs one thing and gets a sensible setup.

**Update**
- **Suggested, not forced.** A new release shows up as an inbox item. Nothing updates on its own, and the PM can pin a version.
- `cairn update --check` previews the change: release notes, breaking changes, checks whose severity changed, overrides that shadow a changed default, and whether a schema migration is needed. If a golden set exists, it runs the eval and shows orphan-claim and error rates before and after.
- `cairn update` applies it. It commits the current state, replaces package-owned files, runs migrations (versioned, idempotent scripts that rewrite frontmatter), updates the lock, and commits again.
- `cairn rollback` restores the previous version and reverts the migration commits.
- **Old Specs stay valid.** Each compile report records the package, skill, and charter versions it ran under. A new check or stricter severity applies to Specs compiled after the update, not retroactively.
- **Versioning:** semantic versions for the package, plus a separate `schema_version` for Thread, Spec, and Overview frontmatter. A schema change always ships with a migration.

**No lock-in**
`cairn remove` deletes package-owned files and host registrations and leaves all content alone. Everything the PM created is plain Markdown and YAML in the repo, and stays readable and useful without the tooling.

**Security**
Releases carry checksums, and the lock records them. Install and update print what they will change before changing it. MCP servers run locally, and credentials stay in the host keystore or git-ignored `.env`, as in section 9.

**Multiple products:** one `.cairn/` per product repo, one shared package cache on the machine.

### 14. Risks and Open Questions
- Distribution: where the package is published (internal registry, git, or both) and which host assistants get a thin wrapper first.
- Org rules: which conditions, if any, deserve a reminder (or a block, if the org requires it). Candidates: restricted data, compliance mandates, public API contract changes. Keep the list short.
- Intake for non-feedback signals: extend theme-extractor or add a separate intake skill for requirement, mandate, and idea signals.
- One Thread to many Specs: decide the split rule (per team, per modality, per release) and whether the compiler runs per Spec with the Thread closing only when all Specs pass.
- Multiple signals per Thread: how a Thread merges or splits when a mandate and related feedback arrive separately.
- Multi-PM conflicts (Thread ownership, charter edits).
- Model drift between versions.
- Adoption by people outside git.
- Small local models on spec generation quality.

### Appendices
A. Frontmatter schemas (Thread, Spec). B. Implementation manifest. C. Readiness check and enablement list (replaces the static Definition of Ready: deterministic items become compiler checks, the rest become the on-demand readiness check). D. Eval harness design. E. Overview template.

### Appendix E: Overview Template
Used for `/architecture/product-overview.md` and each `/architecture/<system>/overview.md`.

```yaml
---
overview_of: <product | system name>
owner: <named person>
source: interview | import | generated-from-schema
verified: false
verified_by: null
last_verified: null
review_ttl: 180d
readiness: L1
---
```

Body sections (any left as `TBD` blocks promotion to L2):
1. Purpose and the problem it solves
2. Users and consumers
3. Boundaries: what it owns, what it does not
4. Interfaces: APIs, events, UI surfaces, with links to contracts
5. Dependencies upstream and downstream
6. Data classes handled and where they flow
7. Constraints: compliance, performance targets, platform limits
8. Known quirks and technical debt (brownfield: required)
9. Non-goals
10. Glossary of product-specific terms
11. Related Threads and Specs (maintained by `mcp-local-tracker`)

---

## Part 2: Compile-Step Validator Spec (`mcp-spec-compiler`)

### Purpose
Deterministic gate between a drafted Spec and `status: Specified`. No LLM calls. It proves a Spec is well-formed and every claim has support. It does not prove the claims are correct, and human review still owns that.

### Inputs
- Draft Spec (`specs/<spec_id>.md`) with structured frontmatter
- Parent Thread file
- `charter.yaml`
- `/signals`, `/library`, `/architecture` indexes (for ref resolution)
- Git history (for Spec hash and acknowledgement checks)

### Spec Frontmatter Contract

```yaml
spec_id: SPEC-042
thread_id: THRD-042
charter_version: 1.3.0
generated_by:
  skill: spec-generator
  skill_version: 0.4.1
  model: <model-id>
sections:
  problem: "..."
  out_of_scope: ["..."]
  error_states: ["..."]
  empty_states: ["..."]
  enablement_deps: ["..."]
slices:
  - id: S1
    name: "Rate-limit responses"
    order: 1
    verify: "Send N+1 requests in the window and confirm a 429 with an error code."
  - id: S2
    name: "Latency target"
    order: 2
    verify: "Run the load profile and confirm p95 is under the threshold."
open_questions:
  - text: "Does the limit apply to internal callers?"
    status: deferred        # answered | deferred | out_of_scope
    reason: "Internal callers use a separate gateway."
    owner: <name>
criteria:
  - id: AC-001
    slice: S1
    type: binary            # binary | threshold
    modality: api           # api | web | mobile
    text: "Endpoint returns 429 when more than N requests arrive in the window."
    trace:
      - ref: feedback:ZD-88421
        basis: interpreted      # direct | interpreted | inferred | decided
        quote: "we keep getting throttled with no error code"   # optional
      - ref: lib:compliance/sec-04#rate-limits
        basis: direct
        quote: "return 429 with a machine-readable error code"
  - id: AC-002
    slice: S2
    type: threshold
    modality: api
    metric: p95_latency
    operator: "<="
    value: 300
    unit: ms
    trace:
      - ref: mandate:MANDATE-Q3
        basis: direct
      - ref: thread:THRD-042#decisions
        basis: decided
        decided_by: <name>      # the 300 ms number was the PM's call, not the mandate's
```

**Trace basis.** A trace proves where a claim came from, not that it's true, and a trace to the Thread can hide an assertion the PM or agent added along the way. Each trace entry therefore says how the criterion relates to its source:

| `basis` | Meaning | Required with it |
|---|---|---|
| `direct` | The source states this | `quote` (checked by C06) |
| `interpreted` | A reasonable restatement of the source (e.g. a complaint turned into a behavior) | `quote` where the source has a usable line |
| `inferred` | Added by reasoning; the source doesn't say it | `assumption`: the id of an assumption or edge case recorded on the Thread or in the Review Brief |
| `decided` | A product decision the PM made | `decided_by` |

A criterion whose traces are all `inferred` rests on no source at all; C23 warns so it reaches the PM.

### Checks

| ID | Check | Severity |
|---|---|---|
| C01 | Frontmatter validates against the Spec schema | Error |
| C02 | Parent Thread exists, lists this Spec in `outbound_refs`, and is `stage: Validating`, `status: Active` | Error |
| C03 | Any approval the PM marked `blocking: true` on the Thread has been recorded as granted | Error (self-imposed blocks only) |
| C04 | Every criterion has at least one `trace` entry | Error |
| C05 | Every `trace.ref` resolves to an existing file and anchor in committed content (never a raw signal copy) | Error |
| C06 | If `quote` is present, it appears in the referenced committed file (whitespace and case normalized). Redacted text cannot be quoted | Error |
| C07 | Criterion `modality` is allowed by the charter (for example, no `web` criteria when UI presence is false) | Error |
| C08 | `binary` criteria contain no vague terms from the lint list (fast, intuitive, user-friendly, appropriate, robust, etc.) and no "should" | Error |
| C09 | `threshold` criteria have metric, operator, numeric value, and unit | Error |
| C10 | Required sections are non-empty: problem, out_of_scope, error_states, empty_states, enablement_deps | Error |
| C11 | Every edge case in the Judge's verdict is mapped to a criterion or listed as deferred with a reason | Error |
| C12 | New numeric literals and identifiers (endpoint paths, field names, limits) in criteria appear in a traced source or the charter | Warn |
| C13 | Validated signals attached to the Thread but cited by no criterion | Warn |
| C14 | Criterion text overlaps heavily with an out-of-scope item | Warn |
| C15 | Skill and charter versions match the pinned `.cairn/package.lock` (no unversioned drafts) | Error |
| C16 | Every cited `/library` or `/architecture` file has `verified: true` and is inside its `review_ttl` | Error if Thread data class is `restricted`, otherwise Warn |
| C17 | Every system in the Thread's `touches` has an overview file (`/architecture/<system>/overview.md`) with a named owner, and the product overview exists | Error |
| C18 | Fast track only: Review Brief exists with skipped gates, ranked verify-first items, and every assumption tagged with an origin; `brief_ack` is recorded after the last Spec edit | Error on `team`, Warn on `solo` |
| C19 | Fast track only: the Thread matches no org rule in `charter.yaml` for a gate being skipped | Warn by default, Error if `enforcement: block` |
| C20 | Clear before it ships: the Spec has no open questions. Each is answered, deferred with a reason and an owner, or moved to out of scope. In fast track, open questions from the Review Brief count | Error |
| C21 | Every criterion belongs to a slice. Every slice has at least one criterion, an order, and a one-line `verify` note saying how it can be confirmed on its own | Error |
| C22 | Spec level, not build level: criteria describe observable behavior and do not prescribe frameworks, databases, or internal structure (terms come from a lint list) | Warn |
| C23 | Every `trace` entry has a `basis` with the field it requires (`direct`: `quote`; `inferred`: `assumption` that resolves; `decided`: `decided_by`). Warn when every trace on a criterion is `inferred` | Error / Warn |

**Legacy waivers:** Threads and Specs tagged `legacy: true` skip C04 and are stamped `legacy_untraced` in the report. C16 still applies. Waivers expire when the Spec is next revised.

Warnings do not block, but each must be acknowledged in frontmatter (`ack: [C12:AC-003 "reason"]`) before the status change.

**Fast-track behavior** (Threads with `track: fast`):

| Check | Normal | Fast track |
|---|---|---|
| C02 | Thread must be `stage: Validating` | Any stage, as long as `track: fast` is set |
| C03 | Self-imposed blocking approvals only | Unchanged. A blocking approval holds until granted or until the PM lifts it |
| C11 | Judge's verdict edge cases mapped | Single-pass critique edge cases mapped or deferred |
| C16 | As listed above | Warn |
| C17 | Error | Warn |
| C18, C19 | Not run | C18: Error on `team`, Warn on `solo`. C19: Warn by default |
| C01, C04 to C10, C15, C20, C21 | Error | Unchanged, still enforced |

A single acknowledgement (`brief_ack`) is bound to the Spec content hash. Editing the Spec after acknowledging invalidates it, so the PM re-acknowledges a changed Spec.

### Outputs
- `compile_report.json` (machine) and `compile_report.md` (human), listing each check, result, and offending criterion IDs.
- On pass: write `compile_report` ref and a **content hash** of the Spec into the Thread, then permit `status: Specified`.
- On fail: no status change. Report lists exactly what to fix.
- Any edit to the Spec after compile changes the hash and invalidates the pass.
- Exit codes: 0 pass, 1 errors, 2 warnings unacknowledged, 3 config or resolution failure.

### How It Plugs In
1. `spec-generator` must emit the frontmatter contract above, so the skill prompt is updated to produce `trace` per criterion.
2. `mcp-local-tracker` refuses `status: Specified` (and `cairn handoff` refuses to deliver) unless a passing report matches the current Spec hash.
3. The same checks run in CI as a pre-merge guard when the repo is shared.
4. The eval harness runs the compiler over golden-set outputs to measure orphan-claim and error rates per skill version.

### Known Limits
- A cited but misread source passes C04 to C06. Mitigation: quote matching where possible, plus engineering review.
- C12 is heuristic and will produce false positives. Tune against the golden set before making it an error.
- C08 lint lists need maintenance as vague terms surface in kickbacks.

### Build Order
1. Schema and C01, C04, C05, C10 (cheap, high value)
2. C06, C07, C08, C09
3. Approval and stage checks (C02, C03, C15), then tracker integration
4. Heuristic checks (C12 to C14) tuned on real Threads
5. Golden-set eval harness
6. C16 and C17, once `onboard-product` has produced readiness levels and overview files
7. Fast track: `fast-track` skill, Review Brief format, `ack-brief` command, C18 and C19. Consider building this earlier, since it is the path the PM will use most day to day.
8. Packaging: package layout, `cairn init`, `cairn doctor`, then `cairn update` with migrations and rollback. Settle the package-owned versus user-owned split first, since it is painful to retrofit.
9. Add-on mechanism and starter sets, once the core is stable. Then add-ons one at a time, starting with the signal adapters and sync targets the pilot needs.
