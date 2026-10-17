---
name: "intake-signal"
description: "Capture a raw input — a quote, directive, bug report, proposal, or analytics number — as a committed signal file under /signals/<type>/, so shape-thread and fast-track have something real to point a Thread's inbound_refs at. The entry point for getting a signal into Cairn before any Thread exists."
argument-hint: "raw text, a pasted quote or ticket, a file/path to import from, or several of these in one call"
metadata:
  product: cairn
  source: "docs/spec-as-code-revision.md Part 1 section 7 (Components) and section 9 (Data Handling and Security)"
user-invocable: true
disable-model-invocation: false
---

## What this does

Turns one raw input into one committed signal file: `signals/<type>/<signal_id>.md`, with the required frontmatter (`signal_id`, `type`, `source`, `captured_on`, `data_class`) and a clean, paraphrased body — the text any later Spec is allowed to quote. Where the original has something worth keeping that the committed copy can't carry (PII, a full ticket thread, source-line detail), it also writes a raw copy to `signals/<type>/raw/<signal_id>.<ext>` (git-ignored).

This is the step before a Thread exists. It never creates or touches a Thread — that's `shape-thread`'s or `fast-track`'s job, once `inbound_refs` can point at a file this skill wrote.

## Required inputs

1. The raw material — pasted text, a short description, a file the PM names, or several of these given together.
2. `charter.yaml`, for `data_class_default`. If it doesn't exist or is still the unfilled stub (see `onboard`), ask which product/repo this signal belongs to rather than guessing a location — don't write into a repo that hasn't been onboarded.
3. Existing files under `signals/<type>/` for each type touched, to pick the next free id without colliding.

## Classifying type (feedback | requirement | mandate | idea | analytics)

- **feedback** — came from a user, a support channel, an app-store review, or a crash/crash-analytics report: something happening *to* users, reported after the fact. Bug and crash reports don't have a cleaner home in this enum — treat them as feedback and say so in the body (see below).
- **requirement** — a scoped ask from a business team, partner, or upstream group outside the PM's own team (sales wants local ads, partnerships wants a roster import, support wants a merge tool). It comes with a named sponsor who can be asked to validate it.
- **mandate** — a directive from leadership, legal, compliance, or an executive. The PM isn't being asked, they're being told, usually with a deadline or a hard constraint (monetization directives, legal/compliance requirements, a competitive response leadership wants shipped).
- **idea** — self-sourced: a dev noticed something, a PM had a thought, an internal proposal nobody outside the team asked for. Tech-debt call-outs the engineering team raises on its own belong here even when they read like requirements — the test is "did anyone outside ask for this, or did the team originate it itself?"
- **analytics** — a number from product data: a funnel drop-off, a conversion or retention rate, an A/B test result, usage telemetry ("Mixpanel shows 40% drop-off at step 3"). It shows *what* users do, not *why*. A crash count belongs here only when the number itself is the point; a single crash report is still feedback.
- When nothing fits cleanly (the recurring case is a bug/crash report), pick the closest type and say explicitly in the body which type was chosen and why, so a later reader isn't misled into thinking it was a clean fit.
- If the choice is genuinely ambiguous and changes which Exploring exit gate later applies (a named sponsor vs. a theme threshold), ask the PM once per batch, not once per item.

## Generating signal_id

- If the raw source already has a natural, stable id (a ticket number, a doc id, a backlog item number), use it as-is (e.g. `ZD-88421`, `TODO-11`).
- Otherwise generate `<PREFIX>-<NNN>`, prefix by type: `FDBK` (feedback), `REQ` (requirement), `MANDATE` (mandate), `IDEA` (idea), `ANLY` (analytics). Find the highest existing `NNN` for that prefix under `signals/<type>/` and increment; start at `001` if none exist.
- Never reuse or renumber an id, even for a file later deleted or rejected.

## Analytics snapshots

A dashboard changes; a Spec must trace to something that doesn't. So an analytics signal is a **snapshot**: the number as it stood when pulled, committed with enough detail that someone else could pull it again.

- Record every field in the analytics block below. Ask the PM for any that's missing rather than guessing. A number with no `period` or no `query` can't be checked, so say so plainly and write `unknown` instead of leaving the field out.
- State the number in the body in a plain sentence (e.g. "40% of sessions that reached step 3 did not reach step 4, 1–30 Sep 2026, n = 12,480 sessions."), so a Spec can quote it verbatim.
- Write down a comparison when there is one: a baseline, the prior period, a target, or the control arm of a test. A lone number with no comparison is still worth capturing, but say in the body that it has none.
- Never store just a link to a live dashboard. The link goes in `query` as context; the number goes in the file. An export (CSV, screenshot) can go in the raw copy.
- Don't explain the number. Why users drop off is a question for the Thread, not a fact for this file.

## Redaction and the raw/committed split

- The committed file is the only thing a Spec may ever quote later — write its body as clean prose an engineer could read verbatim. Paraphrase, don't verbatim-copy, anything containing a name, contact detail, or other PII; strip it, and keep that detail (if worth keeping at all) only in the raw copy.
- Only write a raw copy when the original has something worth keeping that the committed copy can't carry (PII, a full ticket thread, source-line references). A short, already-clean input (a one-line parent quote, a one-paragraph directive) can skip the raw copy entirely.
- Mandates and ideas with no sensitive content can commit the original text directly, per `data_class_default` — no split needed if the charter's data class allows it.
- Default `data_class` to `charter.yaml`'s `data_class_default` unless the content clearly reads as `restricted` (named minors, exact addresses, financial detail) — then say so and ask before committing it anywhere, even redacted.

## Output

For each input, write:

```yaml
---
signal_id: <id>
type: feedback | requirement | mandate | idea | analytics
source: <where this came from, as specific as the PM gave you>
captured_on: <today's date>
data_class: public | internal | restricted
# analytics only:
metric: <what was measured, e.g. "step 3 -> step 4 drop-off">
value: <number>
unit: <%, sessions, seconds, ...>
segment: <who it covers, e.g. "all web sessions"; "all" if unfiltered>
period: <start>..<end>
sample_size: <n and what it counts, or unknown>
comparison: <baseline, prior period, target or control, with its value; or none>
tool: <Mixpanel, Amplitude, GA4, SQL, ...>
query: <saved report link, query text or event names>
pulled_on: <date the number was read>
---

<clean, paraphrased body — this is what later gets quoted>
```

Plus the raw copy at `signals/<type>/raw/<signal_id>.<ext>`, if warranted.

Then tell the PM the ref to use (`<type>:<signal_id>`) for each one, and that the next step is `shape-thread` (or `fast-track`, for something small and well understood) once there's a Thread to point `inbound_refs` at.

## What you must not do

- Do not create or modify a Thread — hand off to `shape-thread`/`fast-track` once the file exists.
- Do not invent or round a metric value, a sample size or a period. A missing field is `unknown`.
- Do not invent a sponsor, a theme count, or anything belonging to the Exploring exit gate — this skill only captures the signal, it never validates or scores it.
- Do not let a committed file quote raw, unredacted text.
- Do not silently resolve an ambiguous type — flag the call in the body, or ask, per Classifying type above.
