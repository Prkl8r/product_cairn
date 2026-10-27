---
name: "check-spec"
description: "Check a drafted Spec by hand against Cairn's compile-step validator rules before the Thread hands it off to engineering. No LLM judgment calls on correctness — only well-formedness and traceability."
argument-hint: "path to the Spec file to check, e.g. specs/SPEC-001.md"
metadata:
  product: cairn
  source: "docs/spec-as-code-revision.md Part 2 (mcp-spec-compiler)"
user-invocable: true
disable-model-invocation: false
---

## What this does

Stands in for `mcp-spec-compiler` until that deterministic server exists. Proves a Spec is well-formed and every claim has support. It does **not** judge whether the claims are correct — that is human/engineering review, and the on-demand readiness check ("is this ready for engineering?"), not this skill.

Be mechanical. Do not soften a failing check because the Spec otherwise reads well, and do not pass something because it "seems fine" — cite the exact line or field for every failure.

## Inputs

Read, in full:
1. The target Spec file.
2. Its parent Thread file (`thread_id` in the Spec must resolve to a real file).
3. `charter.yaml`.
4. Every file any `trace.ref` points to (signals, library, architecture) — resolve each ref to a real committed file and anchor. Never accept a ref into `signals/*/raw/`.

## Run the mechanical checks first

Run `cairn check <spec-id> --markdown`. It runs C01, C02, C04–C10, C20, C21, C23, C27 and C28 as code and prints a row for each. Copy those rows into the report as they are: don't re-derive, soften or override them. Any Fail there is a Fail in the report, and `cairn handoff` refuses the Spec until `cairn check` passes, whatever the report says. If `cairn` isn't installed, run those rules by hand and say so in the report.

Then do the rest by reading: C03, C11–C19, C22, C24–C26 and C29.

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
| C08 | `binary` criteria contain no vague terms (fast, intuitive, user-friendly, appropriate, robust, "should", etc.) and no either/or wording ("either … or", "within or in place of", "and/or") that lets two different outcomes both pass | Error |
| C09 | `threshold` criteria have metric, operator, numeric value, and unit, all present | Error |
| C10 | Required sections are non-empty: `problem`, `out_of_scope`, `error_states`, `empty_states`, `enablement_deps` (or `n/a: <reason>`) | Error |
| C11 | Every edge case from the Framing critique (full jury verdict, or fast-track single-pass critique) is mapped to a criterion or deferred with a reason | Error |
| C12 | Numeric literals and identifiers (endpoints, field names, limits) in criteria appear in a traced source or the charter | Warn |
| C13 | Validated signals attached to the Thread but cited by no criterion | Warn |
| C14 | Criterion text overlaps heavily with an out-of-scope item | Warn |
| C15 | Skill/charter versions match what's pinned (Warn instead of Error if no lock file exists yet) | Error/Warn |
| C16 | Every cited `/library` or `/architecture` file has `verified: true` and is inside its `review_ttl` (a file with none uses `overviews.review_ttl` from `.cairn/config.yaml`, 180d if unset) | Error if Thread `data_class` is `restricted`, else Warn |
| C17 | Every system in the Thread's `touches` has an overview file with a named owner, and the product overview exists | Error normally; **Warn** if `track: fast` or `profile: solo` |
| C18 | Fast track only: Review Brief exists with skipped gates, ranked verify-first items, every assumption tagged with an origin; `brief_ack` is set | Error on `team` profile, Warn on `solo` |
| C19 | Fast track only: Thread matches no org rule for a skipped gate | Warn by default, Error only if that rule sets `enforcement: block` |
| C20 | No open questions remain unresolved: each is `answered`, `deferred` with a reason and owner, or `out_of_scope` | Error |
| C21 | Every criterion belongs to a slice; every slice has ≥1 criterion, an `order`, and a one-line `verify` note | Error |
| C22 | Criteria describe observable behavior, not frameworks/databases/internal structure | Warn |
| C23 | Every `trace` entry has a `basis` (`direct`, `interpreted`, `inferred`, `decided`) with its required field: `direct` needs a `quote`, `inferred` needs an `assumption` id that exists on the Thread or in the Review Brief, `decided` needs `decided_by`. Warn when every trace on a criterion is `inferred` | Error; Warn for all-inferred |
| C24 | Every system in the Thread's `touches` has an overview at `readiness: L2` with `verified: true`. Any other overview (L1, L0, or past its `review_ttl`) never blocks: it produces this Warn, worded exactly as below | Warn (mandatory, can't be acknowledged) |
| C25 | Every trace to an `analytics` signal points at a snapshot with `metric`, `value`, `unit`, `period`, `pulled_on` and `query` set (`unknown` counts as set for `query`, but is listed). A `threshold` criterion that cites an analytics snapshot names the same metric and unit | Error; Warn when `query` is `unknown` or `comparison` is `none` |
| C26 | Every step in a journey this Spec traces to (`journey:<id>#<step>`) is covered by at least one criterion or listed in `out_of_scope`. A `direct` trace never points at a step tagged `origin: inferred` | Warn; Error for a `direct` trace to an inferred step |
| C27 | The parent Thread records a `scope_decision` of `single`, `multi_spec` or `split` (`deferred` or missing fails). Warns when it's `single` and the Spec has four or more slices | Error |
| C28 | Normal track: the parent Thread's `jury_seats` includes a `judge` entry and `verdict_ref` is a file in the repo (warns if the Advocate or Skeptic is missing). Fast track is exempt | Error |
| C29 | Every edge case on the Thread with `needs_decision: true` and `resurface_at: Validating` or `handoff` has a `decision` recorded. A dated one past its date warns too | Warn |

**Several planned Specs.** When the Thread plans more than one Spec, C13 counts a signal as cited if any of the Thread's Specs cites it, and C11 and C26 apply only to the items assigned to this Spec (`planned_spec: <key>` matching this Spec's `planned_spec`). An item assigned to another planned Spec counts as covered when this Spec's `out_of_scope` points to it (`covered by planned Spec <key>` or `by SPEC-NNN`); without the pointer, Warn. An item with no `planned_spec` at all is still checked here as before. Also Warn when a criterion here repeats or contradicts one in another Spec of the same Thread.

For C24, write one line per system, in this exact form, so it reads the same in every report and in the handoff package:

> Warning: Spec relies on unverified L1 Architecture [<system>]. Engineering must verify constraints during estimation.

Use the overview's real readiness in place of `L1` (L0, or "L2, past review_ttl"). A Spec can Pass with C24 warnings, and the PM can't `ack` them away: they stay until the overview reaches L2. `cairn handoff` adds the same lines to the Spec engineering receives.

Skip C02/C03/C15/C16/C17/C18/C19 gracefully (note as N/A, not Fail) only where the repo genuinely has no tooling yet to check them (e.g. no package lock exists) — say so explicitly rather than silently passing.

## Output

Write `compile_report.md` next to the Spec (e.g. `specs/<spec-id>.compile_report.md`) with:
- A table of every check, its result, and the offending ID(s) for any Fail or Warn.
- A one-line verdict, written as a heading `## Verdict: Pass` or `## Verdict: Fail` (`cairn handoff` reads this line). **Pass**: no Errors; Warnings may remain but must be listed. **Fail**: lists exactly what to fix, nothing else implied.
- A count of trace entries by `basis`, so a reader sees at a glance how much of the Spec rests on sources versus inference and decisions. A Pass means every claim has a recorded source; it does not mean the claims are true.
- C24 warnings in their own section, `## Unverified architecture`, listed even when everything else passes.
- Unacknowledged Warnings listed separately. On later runs, Warnings with a matching `ack` entry are listed as acknowledged, with their reason, not as open.

## Walking through the warnings

After writing the report, if any Warning is unacknowledged, offer to go through them: "4 warnings are open. Go through them now? For each one you can acknowledge it or edit the Spec." If the PM says no, stop; the warnings stay listed as open, which never blocks.

C24 is never offered: it can't be acknowledged, only cleared by getting the overview to L2. Say so in one line if any C24 warnings exist.

For each open Warning, in report order, up to three per round:
1. Show what it is in plain words, the offending text (the criterion, quote or number), and why the rule flags it. One or two lines, no rule jargon beyond the id.
2. Offer three choices. In Claude Code, use the question tool (up to three warnings per call):
   - **Acknowledge.** Propose a one-line reason from what you know ("threshold comes from the PM's answer in qa-07, not a source"), which the PM can accept or reword. Never invent one the files don't support; if you have none, ask for it.
   - **Edit.** Propose the specific change to the Spec that would clear it (reword the criterion, add the trace, move the item out of scope). Make the change only after the PM approves the wording.
   - **Leave open.** Nothing changes; it stays on the report.
3. Record acknowledgements in the Spec's frontmatter as `ack: ["C12:AC-003 \"<reason>\""]`, one entry per warning and offending id, appending to any existing list. Never acknowledge a warning the PM didn't explicitly accept.

After each round, say how many are left and ask whether to keep going. When done, re-run the checks touched by any edit (an edit can raise a new Error or Warning) and update the report: the verdict, the open list, and the acknowledged list.

Do not change the Thread's `stage` or `status`, or the Spec's `spec_status`, yourself. Report the verdict. On a Pass, say what the PM can set next:
- **The Thread plans more than one Spec:** `spec_status: specified` on this Spec. It can then be handed off on its own while the Thread stays Active for the rest. Only once every planned Spec is specified or handed off does the Thread become Specified.
- **One Spec:** `status: Specified` on the Thread, as before.

Either way, the Spec becomes handed off when `cairn handoff` sends it.
