# Cairn: The Context-Aware "Spec-as-Code" Workflow Guide

*Threading the needle: just-in-time requirements, from signal to Spec.*

**Product Requirements Document**

> Companion document: `spec-as-code-revision.md` holds the detailed Thread lifecycle, compile-check list, onboarding paths, and install and update design. This PRD states the outcomes and behavior.

**Cairn is the name of the product. A Thread is one unit of work inside it.**

**Flow: Signals -> Threads -> Specs.** Signals are captured, one or more of them feed a Thread, and each Thread is pulled through the gates until it compiles into one or more Specs that engineering picks up.

## 1. Core Problem & Target Outcome
**Problem:** Traditional product management workflows treat specifications as static documents and Jira as the source of truth. When LLMs are introduced to this broken system, they hallucinate because they are asked to write binary engineering contracts (Specs) directly from unstructured signals (customer feedback, requirement docs, mandates, ideas). Furthermore, enablement and GTM training are treated as an afterthought.

**Target Outcome:**
1. **Traceable Handoffs:** Every claim in the final engineering Spec traces to a signal or library reference. A deterministic compile check fails any Spec with unsupported or malformed claims, so deterministic tools govern the rules while the LLM drafts and critiques.
2. **Local-First Tracking (The Repo is the Database):** All project tracking, state management, and status updates happen within the workflow via Markdown YAML frontmatter. External trackers (like Jira or Linear) are optional. At most a few execution fields (status, sprint, assignee) flow back, one-way, into a separate file.
3. **Tool-Agnostic Execution:** The architecture is built on the Model Context Protocol (MCP), so it runs across any compatible AI assistant or IDE.
4. **A Guide, Not a Factory:** The PM drives and the agent advises. Gates are guardrails the PM can step over, nothing runs unless the PM asks, and approvals are recorded when the PM wants them, not enforced. It works for a team product or a solo project.
5. **Clear Before It Ships:** A Spec that reaches Contract has no open questions. Each one is answered, deferred with a reason and an owner, or moved to out of scope.

## 2. Context Tiering & Token Optimization (The Local RAG)
To prevent context-window bloat and stop the LLM from hallucinating irrelevant constraints, Cairn relies on a strict, modular context hierarchy. These files constrain a Thread but never start one.
*   **The Product Charter (`charter.yaml`):** A lightweight root file defining the absolute boundaries of the product: modality, UI presence, profile (`solo` or `team`), write authority, data classification defaults, and optional org rules and approver suggestions. It is versioned.
*   **Modular Architecture Overviews (`/architecture/`):** Atomic markdown files loaded into context only when a Thread explicitly touches those systems (`touches: [system-a]`). Each overview has a named owner and a readiness level (L0 uncharted, L1 drafted, L2 verified). A new product creates its overviews during onboarding. An existing product imports and verifies them gradually, starting with the systems real work touches.
*   **The Reference Library (`/library/`):** A folder of historical specs and compliance guidelines acting as a local RAG repository. Imported files carry provenance and a review window.

## 3. The Thread: State Machine & Lineage Tracking
The core unit of work is a **Thread**. A Thread begins when any **signal** is captured. Signal types are:
*   **feedback:** customer requests, support tickets, Slack threads
*   **requirement:** a requirement doc from a business team or upstream group
*   **mandate:** a corporate, executive, or compliance directive
*   **idea:** an internal idea or proposal, including a shower thought

The Thread is then pulled through progressive gates until it compiles into one or more Specs.

```yaml
---
thread_id: "THRD-042"          # Internal unique identifier (only thread_id, state, owner are required)
state: "Feasibility"           # Signal -> Shape -> Feasibility -> Contract -> Launched (also Parked, Rejected)
owner: "pm_name"
inbound_refs: ["req:REQ-SEC-2026-A", "feedback:ZD-88421", "mandate:MANDATE-Q3"]  # Typed signal refs
outbound_refs: ["Jira-CONN-1402", "Spec-042"]  # Downstream execution targets
touches: ["connectivity-client"]               # Systems whose overviews load as context
---
```

**The Progressive Gates:**
*   **Level 1: Signal (Intake)** -> *Gate: Feedback shows a recurring theme. A requirement, mandate, or idea has a named sponsor who has validated it.*
*   **Level 2: Shape (The 1-Pager)** -> *Decision: proceed, hold (Parked, with open questions and a revisit date), or drop (Rejected, with a reason).*
*   **Level 3: Feasibility (De-Risking)** -> *Gate: Does the logic hold up to edge-case review? Every edge case is mapped to a criterion or deferred with a reason, and every touched system has an overview.*
*   **Level 4: Contract (The Spec)** -> *Gate: Does the Spec pass the compile check (traceability, binary or thresholded criteria, slices, no open questions, charter constraints)?*

**Gates are guardrails, not a prison.** The PM can jump from Level 1 to Level 4 for something quick. The agent backfills the skipped stages in lightweight form and writes a Review Brief: what to verify first, every assumption tagged by origin, open questions, and what was skipped. One acknowledgement is the only checkpoint. The compile check's traceability and well-formedness rules still apply, because they protect engineering from a bad Spec.

**Approvals are recorded, not enforced.** If the PM needs someone's OK, they get it the normal way and, if they want it on record, tell the agent. The agent can draft the ask. The PM can mark an approval as blocking for their own Thread. The tool never gates on approval by default.

## 4. The MCP (Model Context Protocol) Integration Layer
Cairn uses lightweight MCP servers to handle all deterministic actions and state tracking locally.
*   **`mcp-local-tracker` (Core State & Changelog):** Parses YAML frontmatter and Git commit history across all active Threads.
*   **`mcp-signal-ingest` (Level 1):** One adapter per signal type. Feedback adapters fetch from Zendesk or Slack. Requirement and mandate adapters import documents. An idea adapter handles quick capture. Each adapter writes a raw copy to `/signals/<type>/raw/` (git-ignored) and a redacted signal file to `/signals/<type>/<id>.md` (committed) with common frontmatter.
*   **`mcp-library-rag` (Context Routing):** Retrieves specific constraints from `/library/` and `/architecture/` without loading whole folders into context. Explicit `touches` tags route first, and semantic search is added only if the library outgrows tags.
*   **`mcp-spec-compiler` (The Compile Check):** Deterministic, no LLM. Validates a Spec's structure, trace links, criteria quality, slices, and open questions, and binds a pass to the Spec's content hash.
*   **`mcp-external-sync` (Optional):** Creates and updates downstream tickets. Each integration is set to `off`, `suggest`, or `auto` at setup.

## 5. Agentic Skills (The LLM Layer)
Skills are context-aware prompts designed for *generative* and *qualitative* tasks.
*   **`skill: theme_extractor`**: For feedback signals. Deterministic clustering groups feedback, and the LLM only names and summarizes the clusters. Requirement, mandate, and idea signals use a structured intake step instead (problem, sponsor, constraints, success target).
*   **`skill: pm-jury-duty`**: Runs a 3-round adversarial debate (Advocate vs. Skeptic, with the Skeptic on a different model) to output a "Judge's Verdict" of concrete edge cases.
*   **`skill: spec_generator`**: Reads `charter.yaml` and applies strict modality constraints to generate binary or thresholded Acceptance Criteria, each with a trace link and a slice.
*   **`skill: fast-track`**: On the PM's request, backfills skipped stages and writes the Review Brief.
*   **Readiness check (on demand):** "Is this ready for engineering?" reviews a Spec for what the compiler cannot see: ambiguity, contradictions, missing scenarios, and anything an engineer would have to guess.

Anything an agent writes is marked agent-drafted until the PM edits or accepts it.

## 6. LLM Execution & Data Routing (Hybrid Local/API)
Routing follows a data classification field on each Thread (`public`, `internal`, `restricted`), not per-skill rules.
*   **Local Execution (Privacy-First):** Restricted material and proprietary mock payloads are routed to local models (e.g., Ollama running `gemma3`).
*   **API Execution (Heavy Synthesis):** Skills requiring massive context windows are routed to frontier cloud models when the data class allows.

## 7. Enablement & Handoff
*   **Contextual Delivery:** The PM/Agent drafts exact tooltips, macros, or micro-learning scripts that sit inside the GTM team's workflow. Enablement checks are on for the `team` profile and off for `solo`.
*   **Artifact Handoff:** When a Thread achieves `state: "Launched"` locally, enablement artifacts are packaged for GTM deployment. Before launch, any system overview the Spec changed is updated, or marked unchanged.

## 8. The User Experience (UX) Flow: Guiding the PM
The agent's default move at every phase is a short, targeted question or a suggestion, not a finished artifact. The PM can ask for help at any state: "what am I missing?", "argue against this", "find similar past Threads", "tighten these criteria", "is this ready for engineering?", "draft the ask to Sarah."
*   **Phase A: Context Gathering (The Librarian):** A new signal arrives (a customer request via Zendesk, a requirement doc, an executive mandate, or an idea). The PM starts a new **Thread**. The IDE agent pulls related signals (`mcp-signal-ingest`) and cross-references them against constraints (`mcp-library-rag`).
*   **Phase B: Pressure-Testing (The Thought Partner):** The PM drafts a messy 1-Pager. The agent runs `pm-jury-duty` to attack assumptions and surface edge cases.
*   **Phase C: Translating to Spec (The Scribe):** When the PM asks, the agent runs `spec_generator` to translate the Thread context into a strict **Spec**, and the compile check confirms every claim is traceable.
*   **Phase D: Background Housekeeping (The Assistant):** Housekeeping happens through suggestions or choices made once at setup. In `suggest` mode, a one-line item lands in a quiet inbox ("THRD-042 reached Contract. Create the Jira Epic? create / edit first / not this time / never for this product"). It surfaces at natural pauses, never interrupts work, and dismissals stick. In `auto` mode, which the PM opts into per integration, the action runs and is logged in the Thread changelog. Solo projects default to `off` for anything external.

## 9. Success Metrics & Telemetry (KPIs)
These are diagnostics for the PM, not targets to hit. There is no Specs-per-week measure, and nothing compares PMs. Segment every metric by signal type and by track (normal or fast).
*   **Time-to-Spec (Cycle Time):** Elapsed time from a Thread's creation to its compilation into a Level 4 Spec, always read next to kickback rate.
*   **Engineering Defect & Kickback Rate:** Percentage of Specs returned by engineering, by category (missing edge case, ambiguous criterion, wrong constraint, scope change).
*   **Orphan-Claim Rate:** Claims in a Spec with no trace to a signal or library reference, from the compile report. This replaces the Context Preservation Ratio.
*   **Enablement Attach Rate:** Percentage of shipped features that launch with a fully completed GTM enablement asset.
*   **Outcome Metric:** Whether the shipped feature met its stated success target after an agreed period.

Capture baselines for the current process before any pilot.

## 10. Security & Access Boundaries
*   **Secrets Management:** Credentials are managed securely via the host IDE's keystore or local, git-ignored `.env` files.
*   **Repository Write Authority:** Configurable per product in `charter.yaml` (e.g., auto-commit vs. manual PM review).
*   **Signal Data Handling:** Raw signal copies in `/signals/<type>/raw/` are always git-ignored. The redacted signal files (`/signals/<type>/<id>.md`) are committed, so trace refs and quote checks work on a fresh clone or in CI. Mandates and ideas can be committed directly when their data class allows.
*   **LLM Network & Egress Blocks:** Default local execution ensures zero data egress for restricted data. Cloud APIs use explicit network egress blocks as needed.
*   **Org Rules (optional):** If the PM's organization requires sign-off on certain things (restricted data, compliance mandates, public API contract changes), the charter can list them. By default the agent reminds and carries on. `enforcement: block` is for orgs that truly require it.

## 11. Implementation Manifest (Code & Components)
To fully build and deploy Cairn, the following components must be developed:

### A. The Agentic Skills (LLM Instructions)
*These define the AI's behavior and personas. They are saved in the IDE's skill/prompt registry and versioned.*
1.  **`theme-extractor.md`**: Prompt instructions to name and summarize deterministic clusters of feedback signals as root-cause problem statements.
2.  **`pm-jury-duty.md`**: Prompt instructions establishing the "Advocate," "Skeptic," and "Judge" personas, enforcing the 3-round debate format. *(Status: Built)*
3.  **`spec-generator.md`**: Prompt instructions that read `charter.yaml` and translate Thread contexts into strict Level 4 Acceptance Criteria with trace links and slices. *(Status: Built; needs update to emit trace links, slices, and open questions)*
4.  **`fast-track.md`**: Backfills skipped stages and writes the Review Brief.
5.  **`onboard-product` skills**: An import skill for existing products and an interview skill for new products, both producing a charter and product overviews.

### B. Deterministic Scripts (Python MCP Servers)
*These act as the system's hands, strictly governing data flow, search, and API interactions without LLM hallucination.*
1.  **`mcp-local-tracker.py`**: Uses `os`, `yaml`, and `gitpython`. Traverses the local repository to read Thread YAML frontmatter, builds dependency graphs from `inbound_refs`/`outbound_refs`, reads Git logs to render local changelogs, and holds the housekeeping inbox.
2.  **`mcp-signal-ingest.py`**: Uses `requests` and per-type adapters. Fetches or imports signals based on user queries and writes a raw copy to `/signals/<type>/raw/` and a redacted file to `/signals/<type>/<id>.md`.
3.  **`mcp-library-rag.py`**: Indexes `/library` and `/architecture` markdown files. Uses `touches` tags first, with `sqlite-vec` or `sentence-transformers` search only if needed.
4.  **`mcp-external-sync.py`**: Uses the Atlassian Jira or Linear REST APIs. Reads the local Thread state, maps it to a downstream ticket, and writes the Issue ID back to `outbound_refs`. Pulls a few execution fields back one-way into a separate file.
5.  **`mcp-spec-compiler.py`**: Implements the compile checks, writes `compile_report.json` and `.md`, and stamps the Spec content hash.

### C. Configuration Code (State & Boundaries)
*These are the static files that define the rules of the system.*
1.  **`charter.yaml`**: The root configuration file defining product modality (`API`, `Web`, `Mobile`), UI presence (`true`/`false`), profile (`solo`/`team`), Git permissions (`auto_commit: false`), and optional org rules.
2.  **Templates**: Thread, Spec, and Overview boilerplate so `mcp-local-tracker` can index everything.
3.  **`.cairn/config.yaml`**: Integration modes, enforcement setting, dismissed suggestions.

---

## 12. Standard Checklists & Workflows

### A. Engineering Handoff: Readiness
Deterministic items are compile checks. The rest are covered by the on-demand readiness check.
- [ ] Problem statement and business value are explicitly defined
- [ ] Core context, mock data, or PoC logic is documented
- [ ] All acceptance criteria are binary, or carry a stated threshold
- [ ] Every criterion traces to a signal or library reference
- [ ] Criteria are grouped into ordered slices, each verifiable on its own
- [ ] Error states, empty states, and edge cases are defined
- [ ] UX/UI designs or API contract structures are attached
- [ ] Out-of-scope items (what we are NOT building) are explicitly listed
- [ ] No open questions remain (answered, deferred with a reason and owner, or out of scope)
- [ ] Downstream enablement dependencies (docs, training) are identified

### B. Enablement-Driven Feature Workflow
The order is a guide. Skip or reorder what does not apply.
- [ ] Draft 1-Pager Opportunity Brief (Problem, Target, Impact)
- [ ] Get approval where needed and record it (optional, never enforced)
- [ ] Write the Spec: 'The Why', slices, Acceptance Criteria
- [ ] Attach UX designs and technical architecture diagrams
- [ ] Identify enablement dependencies (tooltips, FAQs, docs)
- [ ] Break the Spec into actionable sprint tickets, one set per slice
- [ ] Sync with PMM/Enablement during early sprint demos
- [ ] Record 2-minute micro-learning demo video (e.g., Loom)
- [ ] Embed contextual help into sales/support workflows
- [ ] Conduct internal dogfooding launch with the Support team
- [ ] Execute percentage-based phased user rollout
- [ ] Track feature adoption metrics post-launch
- [ ] Update the Spec, overviews, and charter with retrospective feedback

## 13. Install, Update, and Packaging
Cairn ships as a versioned package that installs into a product repo and updates without touching the PM's content.
*   **Two layers, never mixed:** Package-owned files (skills, servers, checks, schemas, templates, migrations) are replaced on update. User-owned files (charter, signals, Threads, Specs, overviews, library, config, overrides) are never overwritten.
*   **Install:** One command installs the package. `cairn init` in a product repo asks for the profile, creates the skeleton, pins the version in `.cairn/package.lock`, and offers onboarding. It never overwrites files and never edits host config silently. `cairn doctor` verifies the setup.
*   **Add-ons and starter sets:** The core stays small. Signal adapters, sync targets, and export formats are optional add-ons. Starter sets bundle add-ons and defaults by role (PM, enablement, solo builder).
*   **Update:** Suggested through the inbox, never forced, and pinnable. `cairn update --check` previews changes, and `cairn update` applies them with migrations and commits. `cairn rollback` undoes it. Old Specs stay valid.
*   **No lock-in:** `cairn remove` leaves all content, which is plain Markdown and YAML.

See the companion document for the full design.
