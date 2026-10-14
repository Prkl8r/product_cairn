# Cairn Pilot: Dry Run by Hand

*Threading the needle: just-in-time requirements, from signal to Spec.*

**Purpose:** Run one real signal through Cairn's fast track by hand, with no tooling, to find where the design adds friction or misses something before anything is built.
**Time:** 60 to 90 minutes.
**You need:** one product area, one real signal, and an AI assistant that can read the files you paste in.

---

## 1. Pick the slice
- **One product area:** a single system or API, ideally one with an overview you can write or already have.
- **One real signal:** small enough to ship in a sprint or two. Best candidates are feedback with a few tickets behind it, or a short requirement doc. Mandates are a good second run.
- **Profile:** use `team` to feel the full set of checks, or `solo` for the lightest version.

## 2. Set up the folders
```
pilot/
  charter.yaml
  signals/<type>/<signal-id>.md        # redacted, committed
  signals/<type>/raw/<signal-id>.txt   # raw, git-ignored (add signals/*/raw/ to .gitignore)
  architecture/<system>/overview.md
  threads/THRD-001.md
  specs/SPEC-001.md
  friction-log.md
```

**`charter.yaml` (stub)**
```yaml
product: <name>
version: 0.1.0
modality: api            # api | web | mobile
ui_presence: false
profile: team            # solo | team
write_authority: manual  # manual | auto_commit
data_class_default: internal
org_rules: []            # optional, empty is fine
```

**`architecture/<system>/overview.md` (minimum)**
```yaml
---
overview_of: <system>
owner: <name>
source: interview
verified: false
readiness: L1
---
```
Then fill in: purpose, boundaries (what it owns and does not), interfaces, constraints, known quirks. Anything you cannot answer stays `TBD`.

## 3. Capture the signal
**`signals/<type>/<signal-id>.md`**
```yaml
---
signal_id: ZD-88421
type: feedback           # feedback | requirement | mandate | idea
source: <where it came from>
captured_on: <date>
data_class: internal
---
```
Keep the original text in `signals/<type>/raw/<signal-id>.txt` (git-ignored). Paste a redacted version below the frontmatter, so quotes and trace refs can be checked from committed files only. If there are several related signals, make one file each.

## 4. Start the Thread
**`threads/THRD-001.md`**
```yaml
---
thread_id: THRD-001
state: Signal
owner: <you>
inbound_refs: ["feedback:ZD-88421"]
touches: ["<system>"]
---
```
Add one paragraph in your own words: what this is and why it matters. This is the only writing required before fast track.

## 5. Run the fast track
Paste this into your assistant along with the charter, the overview, and the signal files.

> You are acting as Cairn's fast-track skill. I own this Thread and I am asking you to take it from Signal to a compiled Spec.
>
> Rules:
> 1. Before drafting, ask me up to 3 questions, and only questions whose answers would change the Spec.
> 2. Backfill the skipped stages in light form: a short problem and impact brief, a single-pass critique with the top edge cases, then the Spec.
> 3. Every acceptance criterion must be binary, or carry a threshold (metric, operator, number, unit), and must have at least one trace to a signal or library file. Quote the source where you can.
> 4. Group criteria into ordered slices. Each slice gets a one-line way to verify it on its own.
> 5. Do not invent numbers, endpoints, field names, or limits. If you need one that no source gives me, ask me or list it as an open question.
> 6. Describe observable behavior, not how to build it.
> 7. Mark everything you wrote as agent-drafted.
> 8. Finish with a Review Brief: the 3 to 5 things I should verify first, every assumption tagged `signal`, `overview`, `library`, or `inferred`, open questions, and what was skipped. If you think this should not be fast-tracked, say so, then proceed anyway.

**Spec skeleton to ask for** (`specs/SPEC-001.md`)
```yaml
---
spec_id: SPEC-001
thread_id: THRD-001
charter_version: 0.1.0
track: fast
skipped_gates: [Shape, Feasibility]
sections:
  problem: "..."
  out_of_scope: ["..."]
  error_states: ["..."]
  empty_states: ["..."]
  enablement_deps: ["..."]   # or "n/a: <reason>"
slices:
  - id: S1
    name: "..."
    order: 1
    verify: "..."
open_questions: []           # each: text, status (answered | deferred | out_of_scope), reason, owner
criteria:
  - id: AC-001
    slice: S1
    type: binary             # binary | threshold
    modality: api
    text: "..."
    trace:
      - ref: feedback:ZD-88421
        quote: "..."         # optional
review_brief:
  verify_first: []
  assumptions: []            # each: id, text, origin
  open_questions: []
brief_ack: <set when you acknowledge>
---
```

## 6. Review the Brief
- Read "verify first" before anything else. Did it point at the real risks?
- Check every assumption tagged `inferred`. Keep, correct, or move to an open question.
- Edit anything you disagree with. Edited text is now yours.

## 7. Compile by hand
Check each item. Any "no" is a fix or a note in the friction log.

| Check | Question |
|---|---|
| Structure | Does the frontmatter match the skeleton, with required sections filled (or `n/a` with a reason)? |
| Trace | Does every criterion have at least one trace, and does each ref point to a real file? |
| Quotes | Does every quote appear in its source? |
| Criteria quality | Are all criteria binary or thresholded, with no vague words (fast, intuitive, robust, appropriate, "should")? |
| Slices | Does every criterion sit in a slice, and does every slice have a verify line? |
| Charter | Does anything conflict with the charter (modality, UI presence, org rules)? |
| Invented facts | Does any number, endpoint, or field name appear in no source? |
| Clear before it ships | Is every open question answered, deferred with a reason and owner, or out of scope? |
| Contract level | Do criteria avoid prescribing frameworks or internal structure? |

Then acknowledge the Brief (write today's date and your initials in `brief_ack`).

## 8. Hand it off
Give the Spec to an engineer, or to a coding agent, and ask them to read it cold. Record every question they ask. Each question is either a gap in the Spec or a gap in Cairn.

## 9. Friction log
Fill in as you go. Keep it blunt.

| Step | What I did | Felt heavy? | Missing? | Idea |
|---|---|---|---|---|
| Capture the signal | | | | |
| Start the Thread | | | | |
| Fast track prompt | | | | |
| Review the Brief | | | | |
| Compile by hand | | | | |
| Handoff | | | | |

## 10. Judge it
Answer these when you finish.
1. Did the Review Brief point at the real risks, or at noise?
2. How many criteria had no real trace? How many numbers or names did the agent invent?
3. Which fields or checks did you not need? Those are candidates to cut or make optional.
4. Did any check feel like policing instead of help?
5. How did the time compare with how you would normally get to a Spec?
6. What did the engineer ask that the Spec should have answered?
7. Would you do it again for the next small piece of work? What would make you skip it?

If the answers to 3, 4, and 7 are lopsided, change the design before building anything.
