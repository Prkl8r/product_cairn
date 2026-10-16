---
name: "compile-check"
description: "Check a drafted Spec by hand against Cairn's compile-step validator rules before the Thread hands it off to engineering. No LLM judgment calls on correctness — only well-formedness and traceability."
argument-hint: "path to the Spec file to check, e.g. specs/SPEC-001.md"
metadata:
  product: cairn
  source: "docs/cairn-pilot-walkthrough.md step 7, docs/spec-as-code-revision.md Part 2 (mcp-spec-compiler)"
user-invocable: true
disable-model-invocation: false
---

## What this does

Stands in for `mcp-spec-compiler` during the pilot, since no deterministic server exists yet. Proves a Spec is well-formed and every claim has support. It does **not** judge whether the claims are correct — that is human/engineering review, and the on-demand readiness check ("is this ready for engineering?"), not this skill.

Be mechanical. Do not soften a failing check because the Spec otherwise reads well, and do not pass something because it "seems fine" — cite the exact line or field for every failure.

## Inputs

Read, in full:
1. The target Spec file.
2. Its parent Thread file (`thread_id` in the Spec must resolve to a real file).
3. `charter.yaml`.
4. Every file any `trace.ref` points to (signals, library, architecture) — resolve each ref to a real committed file and anchor. Never accept a ref into `signals/*/raw/`.

## Checks

Run every check below against the Spec. For each, record **Pass**, **Fail**, or **Warn**, with the offending criterion/section ID when it fails.

| ID | Check | Severity |
|---|---|---|
| C01 | Frontmatter matches the Spec schema (all required keys present, correctly typed) | Error |
| C02 | Parent Thread exists and lists this Spec in `outbound_refs`. Normal track: Thread is `stage: Validating`, `status: Active`. Fast track (`track: fast`): any stage is fine | Error |
| C03 | Any approval the PM marked `blocking: true` on the Thread is recorded as granted | Error |
| C04 | Every criterion has at least one `trace` entry (waived only if `legacy: true`, stamp `legacy_untraced`) | Error |
| C05 | Every `trace.ref` resolves to an existing committed file and anchor — never a raw signal copy | Error |
| C06 | Every `quote`, if present, appears verbatim (whitespace/case normalized) in the referenced committed file | Error |
| C07 | Criterion `modality` is allowed by the charter (e.g. no `web` criteria when `ui_presence: false`) | Error |
| C08 | `binary` criteria contain no vague terms (fast, intuitive, user-friendly, appropriate, robust, "should", etc.) | Error |
| C09 | `threshold` criteria have metric, operator, numeric value, and unit, all present | Error |
| C10 | Required sections are non-empty: `problem`, `out_of_scope`, `error_states`, `empty_states`, `enablement_deps` (or `n/a: <reason>`) | Error |
| C11 | Every edge case from the Framing critique (full jury verdict, or fast-track single-pass critique) is mapped to a criterion or deferred with a reason | Error |
| C12 | Numeric literals and identifiers (endpoints, field names, limits) in criteria appear in a traced source or the charter | Warn |
| C13 | Validated signals attached to the Thread but cited by no criterion | Warn |
| C14 | Criterion text overlaps heavily with an out-of-scope item | Warn |
| C15 | Skill/charter versions match what's pinned (note if no lock file exists yet during pilot — Warn instead of Error) | Error/Warn |
| C16 | Every cited `/library` or `/architecture` file has `verified: true` and is inside its `review_ttl` | Error if Thread `data_class` is `restricted`, else Warn |
| C17 | Every system in the Thread's `touches` has an overview file with a named owner, and the product overview exists | Error normally; **Warn** if `track: fast` or `profile: solo` |
| C18 | Fast track only: Review Brief exists with skipped gates, ranked verify-first items, every assumption tagged with an origin; `brief_ack` is set | Error on `team` profile, Warn on `solo` |
| C19 | Fast track only: Thread matches no org rule for a skipped gate | Warn by default, Error only if that rule sets `enforcement: block` |
| C20 | No open questions remain unresolved: each is `answered`, `deferred` with a reason and owner, or `out_of_scope` | Error |
| C21 | Every criterion belongs to a slice; every slice has ≥1 criterion, an `order`, and a one-line `verify` note | Error |
| C22 | Criteria describe observable behavior, not frameworks/databases/internal structure | Warn |

Skip C02/C03/C15/C16/C17/C18/C19 gracefully (note as N/A, not Fail) only where the pilot genuinely has no tooling yet to check them (e.g. no package lock exists) — say so explicitly rather than silently passing.

## Output

Write `compile_report.md` next to the Spec (e.g. `specs/<spec-id>.compile_report.md`) with:
- A table of every check, its result, and the offending ID(s) for any Fail or Warn.
- A one-line verdict, written as a heading `## Verdict: Pass` or `## Verdict: Fail` (`cairn handoff` reads this line). **Pass**: no Errors; Warnings may remain but must be listed. **Fail**: lists exactly what to fix, nothing else implied.
- Unacknowledged Warnings listed separately so the PM can add `ack: [C12:AC-003 "reason"]` style entries if they choose to proceed anyway.

Do not change the Thread's `stage` or `status` yourself. Report the verdict; on a Pass, the PM may set `status: Specified` (the Spec is ready); it becomes `Handed off` when it goes out.
