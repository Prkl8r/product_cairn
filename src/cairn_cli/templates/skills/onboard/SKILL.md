---
name: "onboard"
description: "The one entry point before any Thread can exist: ratify a charter.yaml and draft product/system overviews, either by pulling context from a codebase and/or a connected tracker (brownfield) or by running an interview (greenfield, --new)."
argument-hint: "--new for a greenfield interview; or a codebase path / tracker connection to pull context from for an existing product (brownfield import)"
metadata:
  product: cairn
  source: "docs/spec-as-code-revision.md Part 1 section 6 (Product Onboarding) and Appendix E (Overview Template)"
user-invocable: true
disable-model-invocation: false
---

## What this does

Produces a ratified `charter.yaml` plus a product overview and one overview per system, each at a known readiness level (L0 uncharted, L1 drafted or imported, L2 verified by a named owner). Two paths end in the same state:

- **Brownfield** (default): an existing product. Pull from whatever is actually available — a codebase, a connected tracker (Jira, Linear, ClickUp, Monday, Asana, or whatever this environment has configured), old specs, wiki pages, OpenAPI files, architecture docs — and propose `charter.yaml` and overviews from it. The PM should have to hand you as little as possible; go find it first, and only ask for what you genuinely can't pull or infer.
- **Greenfield** (`--new`): a new product with no material to import. Run an interview instead and draft from the answers.

Nothing else in Cairn can run meaningfully without this. `shape-thread`, `fast-track`, and `assess-thread` all read `charter.yaml` and `architecture/<system>/overview.md` — before those exist, there is nothing to check modality, profile, write authority, or touched systems against. This runs once per product, before the first real Thread.

## Which path

If `charter.yaml` exists, check whether it's actually filled in before treating this as a repeat onboarding. `cairn init` seeds every repo with a stub `charter.yaml` (every field `TBD`) — a stub is not a ratified charter, so treat it the same as a missing file, not as evidence onboarding already happened.

- **No `charter.yaml`, or one that's still the unfilled stub:** this is a fresh onboarding. If no `--new` flag was given, ask whether there's existing material to import before assuming brownfield — don't default to greenfield just because nothing was specified.
- **A `charter.yaml` with real values filled in:** this is not a fresh onboarding — stop and ask what the PM actually wants (add one system's overview, revise the charter) rather than redrafting everything.

## Path A: Brownfield (existing product)

### Required inputs
At least one of: a codebase (a path or the current repo), a connected tracker (Jira/Linear/ClickUp/Monday/Asana/etc.), or docs/specs/wikis/OpenAPI files the PM points you at. Nothing else needs to pre-exist — this is the first skill in the product's life. If the PM gives you nothing at all, ask which of these exist before falling back to the greenfield interview — brownfield pulls beat a cold interview whenever there's something to pull from.

### Pulling context automatically
Go get this yourself before asking the PM for it. Everything pulled here is still source material, not fact — it feeds the same `source`/`verified: false`/L1 treatment as anything else in this path, and every claim you draft from it should be easy for the PM to check fast (cite the file path, line, or issue key it came from).

**Confirm scope first.** A codebase or tracker instance can span many products. Before scanning, confirm what this `charter.yaml` is actually for (one repo, one service, one tracker project/board) — do not silently scan a whole monorepo or an entire Jira instance and merge everything into one charter.

**Codebase scan** (when given a repo path, or run from inside one):
1. Read `README`, `CONTRIBUTING`, and any top-level `/docs` for stated purpose, users, and non-goals.
2. Read manifest files (`package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml`, `pom.xml`) for the product name, version, and declared dependencies.
3. Infer candidate **systems** from top-level directory structure (`src/`, `services/`, `apps/`, `packages/`) — one overview candidate per clearly separate service or module, not per file.
4. Find OpenAPI/Swagger/GraphQL/proto schema files and generate the Interfaces section from them directly (per rule A3) rather than drafting on top.
5. Check infra-as-code (`docker-compose.yml`, k8s manifests, Terraform) for service boundaries, dependencies between systems, and deployment modality clues (web/api/mobile).
6. Grep for `TODO`/`FIXME`/`HACK` comments and any existing architecture notes as candidate "Known quirks" content — flag, don't resolve.
7. Infer `ui_presence` and `modality` from what's actually there (a frontend framework and routes present vs. an API-only service with no UI code) and cite the specific files that told you.
8. Treat anything inferred this way as `source: import`, origin-tagged, and never silently promoted past L1.

**Tracker scan** (when a tracker is connected — Jira, Linear, ClickUp, Monday, Asana, etc.):
1. If more than one tracker connector is available, or none is authenticated yet, ask the PM which one and complete that connector's authentication step first — don't guess which tracker is the right one.
2. Pull the project/board list and ask the PM to confirm which project(s) map to this product, rather than assuming.
3. Use open epics and issues to corroborate or propose candidate systems, and to find named owners/assignees as candidate overview `owner`s — but a tracker assignee is a *candidate* owner, not a ratified one.
4. Pull in-flight (open, not closed) epics/issues as candidates for the legacy-ticket-import step (rule A6): convert each into a Thread at the matching `stage` and `status`, tagged `legacy: true`, with the issue key in `inbound_refs`.
5. Do not pull closed/historical issues into Threads — they stay in the tracker (rule A9 still applies: old tickets are internal artifacts, never feedback signals).
6. If an issue body contains data that looks `restricted` (customer PII, credentials, compliance-flagged content), do not copy it verbatim into a committed overview or Thread — summarize and flag the classification instead, same as any other restricted signal.

### Rules
1. **Charter first.** Read the source material and propose `charter.yaml`: `product`, `version`, `modality` (`api`/`web`/`mobile`), `ui_presence`, `profile` (`solo`/`team`), `write_authority` (`manual`/`auto_commit`), `data_class_default`, `org_rules`. Don't infer modality or profile from a vibe — cite what in the material told you, and ask for anything you can't ground. The PM ratifies by hand (edits the draft themselves, or tells you explicitly to proceed); you never write it as settled on your own.
2. Import into `/library` (historical specs, compliance docs) and `/architecture` (system overviews). Every imported file gets provenance frontmatter: `source`, `imported_on`, `owner`, `verified: false`, `last_verified`, `review_ttl`. Use the Appendix E template below for overviews.
3. Where a deterministic source exists (an OpenAPI file, a schema), generate the Interfaces section from it directly and summarize — don't draft interface content on top of a spec that already states it exactly.
4. Every overview needs a named `owner` before it can move past L1. If the PM hasn't named one, leave the field blank and say so plainly — an unowned overview can never reach L2.
5. Everything produced here starts at readiness **L1** (drafted or imported, not verified), no matter how authoritative the source material looked. Never set `verified: true` yourself; that is the named owner's call, made explicitly.
6. If the PM wants open tickets/epics represented, convert each into a Thread at the `stage` and `status` matching reality, tag it `legacy: true`, and put the ticket key in `inbound_refs`. Leave closed/historical tickets where they already live — do not backfill history into Threads.
7. Write known debt and as-built quirks into each overview's "Known quirks" section without skipping it to save time — undocumented current behavior is the most common cause of brownfield kickbacks later.
8. Scope to what's about to matter. Don't try to overview the whole codebase in one pass; recommend starting with the one slice (one API, one client, one system) that real work is about to touch, and get that slice to L2 before moving on. Name what got skipped and why, so it isn't mistaken for "already covered."
9. Do not treat old tickets as feedback signals. They are internal artifacts, not customer signal, and belong in `touches`/history, not `inbound_refs` of type `feedback`.

## Path B: Greenfield (new product, `--new`)

### Required inputs
None exist yet — the PM's own answers are the only source.

### Rules
1. Ask for: purpose, target users, modality, UI presence, profile (`solo`/`team`), boundaries, key systems, interfaces, dependencies, data classes, success targets, non-goals, and a named owner per system. A conversational back-and-forth is fine; filling in a field the PM hasn't answered is not.
2. **Do not invent content.** Any field the PM leaves unanswered stays `TBD`, visibly, in the file — never silently dropped, never guessed to keep things looking complete.
3. Produce a draft `charter.yaml`, `/architecture/product-overview.md`, and one `/architecture/<system>/overview.md` per named system, all stamped `source: interview`.
4. Any `TBD` field blocks that overview's promotion to L2 — say this plainly rather than letting it slide through by omission.
5. The PM or a named architect ratifies each overview to L2 explicitly (`verified: true`, `verified_by`, `last_verified`, each set by them, not by you).

## Shared output (both paths)

- `charter.yaml` — draft, pending the PM's ratification.
- `/architecture/product-overview.md`.
- `/architecture/<system>/overview.md`, one per system, with this frontmatter:
  ```yaml
  overview_of: <product | system name>
  owner: <named person>
  source: interview | import | generated-from-schema
  verified: false
  verified_by: null
  last_verified: null
  review_ttl: 180d
  readiness: L1
  ```
  Body: Purpose, Users/consumers, Boundaries, Interfaces, Dependencies, Data classes, Constraints, Known quirks (brownfield: required), Non-goals, Glossary, Related Threads/Specs.
- A short close-out summary: what's at L1 and ready to use as-is, what's still `TBD` or unowned, and exactly what the PM needs to do to ratify the charter and reach L2 on the systems that matter now.

## What you must not do

- Do not set `verified: true` or otherwise move any overview past L1 yourself — only a named human does that.
- Do not write `charter.yaml` as ratified without the PM's explicit say-so; until then it is a draft, clearly labeled.
- Do not create or touch anything under `threads/` or `specs/` — this skill's job ends at the charter and overviews, with the single exception of the brownfield legacy-ticket import (rule A6), which is explicitly allowed to create `legacy: true` Threads.
- Do not invent purpose, boundaries, or interface content that isn't grounded in the source material (pulled or handed to you) or the PM's own answers. Label anything you had to infer, and ask rather than assume for anything that changes modality, profile, or write authority.
- Do not scan or query beyond the scope the PM confirmed (rule: "Confirm scope first") — a wider codebase or tracker instance than the product being onboarded is out of bounds, not free context.
- Do not copy tracker content that looks `restricted` into a committed file verbatim — summarize it and flag the classification instead.
