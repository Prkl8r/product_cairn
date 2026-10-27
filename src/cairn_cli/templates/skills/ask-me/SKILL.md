---
name: "ask-me"
description: "Fill in a Thread by asking the PM questions, three at a time, multiple choice or free form, aimed at whatever the Thread is missing for its stage: the problem and evidence early on, then users and use cases, then acceptance criteria, thresholds, and error and empty states. Records each answer on the Thread so later skills can trace to it. After each round it asks whether the PM is up for another three, and only continues on a yes."
argument-hint: "thread id, and optionally a focus (e.g. \"use cases\", \"acceptance criteria\", \"error states\")"
metadata:
  product: cairn
  source: "README (core flow); check-spec C10, C20 and C23"
user-invocable: true
disable-model-invocation: false
---

## What this does

Asks the PM questions to get more detail into a Thread, three at a time. Each round targets the biggest gaps for the Thread's stage, records the answers on the Thread, and then asks whether the PM is up for another three questions. Answers are the PM's own decisions, so a Spec can trace to them with `basis: decided` (`check-spec` C23).

Usable at any stage, on its own or between steps of the core flow. It never moves the Thread on; it only fills it in.

## Required inputs

1. The Thread file, any stage, `status: Active`. For a Parked, Rejected or Handed-off Thread, say so and ask whether to continue anyway.
2. Everything already on the Thread: brief, `## Q&A`, `use_cases`, verdict, `planned_specs`, `## Open items`, and anything in `outbound_refs` that resolves to a file (journeys, mocks, API specs, drafted Specs).
3. The signals in `inbound_refs` and the overviews for systems in `touches`, so you don't ask what they already answer.
4. `charter.yaml`, so you don't ask what the charter settles (modality, UI presence, data class).

If the PM gave a focus, ask about that first.

## Choosing what to ask

Before each round, list what's missing and rank it by how much it would change the Spec. Ask about the top three. Never ask something the files already answer; if a file answers it but might be out of date, ask the PM to confirm it in one question.

What usually matters, by stage:

| Stage | Look for |
|---|---|
| **Exploring** | Who's affected and how often; how strong the evidence is; workarounds people use today; why now; what outcome would show this worked, and how it's measured |
| **Framing** | Use cases: who, in what situation, wanting what; which use cases are in and out of scope; constraints from other teams or systems; risks the PM already suspects |
| **Validating** | Acceptance criteria: what must be true for each use case, pass/fail or with a number (metric, operator, value, unit); error and empty states; limits and volumes; what's explicitly out of scope; open questions blocking a criterion (C20) |
| **Specified / Handed off** | Only what a kickback or a reviewer raised |

Also look at what other skills have already flagged: unmapped edge cases, inferred journey steps, `unknown` in the brief, deferred open questions with no owner.

## Rules

1. **Three questions per round, no more.** If fewer than three gaps matter, ask fewer and say why.
2. **Pick the style per question:**
   - **Multiple choice** when the likely answers are known: 2–4 options, each with a one-line consequence (what picking it means for the Spec), and the most likely first. Free text is always allowed as "Other".
   - **Free form** when options would put words in the PM's mouth: evidence, who's affected, why now, a number you have no basis for.
   - Never offer made-up numbers as options. Options for a threshold come from a signal, overview, analytics snapshot or charter, and say which; otherwise ask free form.
3. **Ask, don't lead.** Phrase questions neutrally. When you have a recommendation, label it "(recommended)" and give the reason in one line.
4. **In Claude Code, ask with the question tool** (one call per round, all three questions in it). Elsewhere, write a numbered list, with lettered options for multiple choice, and wait for the answers.
5. **Record every answer before the next round** (see Output). If an answer contradicts a signal, overview or earlier answer, say so and ask which stands; don't silently overwrite.
6. **End every round by asking whether the PM is up for another three questions.** First say what got filled and what's still missing, in two or three lines. Then ask, naming what the next three would cover, e.g. "Up for another 3 questions? Next: error states for import, the size limit, and who owns the sync." Offer: **yes**, **yes, but focus on something else** (the PM names it), or **stop for now**. In Claude Code, ask this with the question tool too. Never start the next round without a yes. If nothing left would change the Spec, say so and suggest the next skill instead of asking.
7. Don't decide for the PM. "Don't know" is a valid answer: record it as an open question with an owner if the PM names one.
8. Mark what you write from answers as agent-drafted until the PM accepts it, except the answers themselves, which are the PM's words.

## Output

Append each round to a `## Q&A` section in the Thread body (create it if missing), one entry per question, numbered across rounds so a Spec can point at it (`thread:THRD-001#qa-07`):

```markdown
## Q&A

### qa-07
- **Asked:** 2026-10-27, Validating, focus: acceptance criteria
- **Q:** How long can an import of a 500-row roster take before it counts as failed?
- **Options:** A) 30 s (from `analytics:ANLY-004` p95)  B) 60 s  C) no limit, show progress
- **A:** B, 60 s. "Support says people give up after a minute." (PM)
```

Then fold the answer into the Thread's structured fields when there's a place for it:

```yaml
use_cases:                 # from Framing answers
  - id: UC-01
    actor: "..."
    situation: "..."
    wants: "..."
    in_scope: true
    source: thread:THRD-001#qa-03
candidate_criteria:        # from Validating answers; draft-spec turns these into real criteria
  - use_case: UC-01
    text: "..."
    type: binary | threshold
    threshold: {metric: ..., operator: ..., value: ..., unit: ...}   # threshold only, from the PM's answer
    source: thread:THRD-001#qa-07
open_questions:            # "don't know" answers
  - text: "..."
    owner: "..."
    source: thread:THRD-001#qa-08
```

Answers that belong in the brief (evidence, why now, expected outcome) update the brief, citing the `qa-NN` entry. A new risk goes in `## Open items` for the jury. If an answer adds a whole new outcome to the Thread, run `shape-thread`'s Scope check before the next round.

## How other skills use it

`draft-spec` and `fast-track` turn `use_cases` and `candidate_criteria` into Spec criteria, tracing each to its `qa-NN` entry with `basis: decided` and `decided_by` set to the PM. `map-journey` can build steps from use cases. `fast-track`'s up-front questions follow this skill's rules for style and recording.

## What you must not do

- Do not change the Thread's stage, status or track.
- Do not draft the Spec or write criteria into one; `candidate_criteria` on the Thread is as far as this goes.
- Do not ask more than three questions in a round, or ask again what's already answered.
- Do not invent options, numbers or quotes, and never put words in the PM's answer.
