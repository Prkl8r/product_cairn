---
name: "park-or-reject"
description: "Park a Thread (on hold, with what has to be true before it's picked up again) or reject it (with a reason and category), at any stage. Also resumes a Parked Thread. Only updates the Thread's status (its stage is kept), never deletes anything."
argument-hint: "thread id, then park / reject / resume, plus the reason if you have it"
metadata:
  product: cairn
  source: "specs/001-thread-fidelity-stages/spec.md (Status)"
user-invocable: true
disable-model-invocation: false
---

## What this does

Takes a Thread off the active path at any stage, not only at the end of Exploring (where `shape-thread` already offers hold/drop). It changes `status` only; `stage` stays where it was, so the Thread keeps the fidelity it reached. It records a fact and a reason so nobody argues the same idea again from scratch later.

- **Park** means "not now". Record what has to happen or change before it's worth picking up.
- **Reject** means "no". Record why, with a category.
- **Resume** sets a Parked Thread back to `status: Active`, at the stage it was parked in.

## Required inputs

1. The Thread file. Any status except `Rejected` can be parked or rejected. Only `Parked` can be resumed.
2. Park or reject. If the PM's wording is unclear ("let's drop this for now"), ask which one they mean. "For now" usually means park.
3. For **park**: what needs to happen or change first. Ask once, with examples so it's quick to answer: "when the payments API ships", "after Q1 planning", "if three more customers ask". A date is optional. A condition is more useful. If the PM doesn't know, record `pickup_when: unknown` and move on. Don't press.
4. For **reject**: the reason in the PM's own words, and a category. Ask for the category if it isn't clear from what they said:
   - `duplicate`: another Thread already covers this. Ask which one.
   - `superseded`: a newer Thread or decision replaced it. Ask which one, if there is one.
   - `out_of_scope`: outside the charter, strategy, or product boundaries.
   - `low_value`: real, but impact too small for the cost.
   - `not_feasible`: technical, legal, or resource constraints rule it out.
   - `no_sponsor`: the sponsor withdrew, or nobody will validate it.
   - `other`: none of the above. The reason text carries it.

## Rules

1. Never pick the reject category yourself when it's ambiguous. Categories feed reporting, so ask.
2. Parking keeps everything: Specs, verdicts, open items. Resuming should feel like picking up where things left off.
3. On **resume**, set `status: Active`. Keep the park fields as history, and add a `resumed_on` date. If what the Thread was waiting on (`pickup_when`) clearly hasn't happened, say so once, then do what the PM asks.
4. A Rejected Thread is reopened only when the PM explicitly asks. Set `status: Active` (stage unchanged), keep the reject fields, and add `reopened_on` and `reopen_reason`.
5. For `duplicate` or `superseded`, offer to tie the Threads together with `bundle-threads`. Don't do it automatically.
6. **Parking or rejecting applies to the whole Thread,** with every planned Spec in it. If the PM wants to stop only one planned Spec, don't park the Thread. Offer two choices: split that part into its own Thread (`shape-thread`'s Scope check, option 2) and park or reject that one, or drop it from `planned_specs` with a one-line reason kept in the `## Planned Specs` table. A Spec that's already `handed_off` stays handed off either way; say so.
6. If a Spec from this Thread already went to engineering (the Thread is `status: Handed off`), say so before parking or rejecting. Engineering may need to be told, and that's the PM's call.

## Output

Update the Thread file's frontmatter. Park:

```yaml
status: Parked               # stage is left as it was
parked_on: <date>
reason: "..."                # why not now
pickup_when: "..."           # what has to happen or change first, or "unknown"
revisit_date: <date>         # optional
```

Reject:

```yaml
status: Rejected             # stage is left as it was
rejected_on: <date>
reason: "..."
reject_category: duplicate | superseded | out_of_scope | low_value | not_feasible | no_sponsor | other
see_thread: THRD-NNN         # duplicate / superseded only, when known
```

Then tell the PM in one line what changed. For a park, include what it's waiting on.

## What you must not do

- Do not delete or move the Thread, its Spec, or its signals. Status changes only.
- Do not guess a `pickup_when` condition or a reject reason the PM didn't give.
- Do not change other Threads, even a duplicate's. Offer `bundle-threads` instead.
