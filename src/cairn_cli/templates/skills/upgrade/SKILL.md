---
name: "upgrade"
description: "Bring a product repo up to the installed Cairn version in one go: refresh the skills, apply the safe fixes, then ask the PM only what can't be worked out (a Thread's scope, whether its jury really ran), and record the answers so `cairn check` passes again."
argument-hint: "nothing needed; run it after updating the cairn CLI"
metadata:
  product: cairn
  source: "0.8 gate rules C27 (scope decision) and C28 (jury record)"
user-invocable: true
disable-model-invocation: false
---

## What this does

One step for the PM after a Cairn update. Newer versions can add rules that older Threads don't meet yet. This skill updates the installed skills, fixes what has only one right answer, and turns everything else into a few quick questions. The PM shouldn't need to know rule numbers or edit YAML.

## Steps

1. **Refresh the install.** Run `cairn init --here --force --skills-only`. It updates the skill files and never touches `charter.yaml`, signals, Threads or Specs. Say in one line which version the repo is now on (`cairn version`).
2. **Apply the safe fixes.** Run `cairn doctor --fix`. It records `scope_decision: single` on Validating Threads that have one Spec and no planned Specs, the only possible answer. Don't list each fix; say how many Threads it fixed.
3. **Find what's left.** Run `cairn doctor --gaps-json`. Each entry names a `thread`, a `rule` and a `kind`. If `gaps` is empty, say "All Threads are up to date" and stop.
4. **Ask the PM, grouped by Thread**, at most three questions at a time, multiple choice where possible. Open each Thread's file first so the question can name what it's about in plain words (its title or problem line), not just its id.

### `ask_scope`: the Thread has several Specs (or `scope_decision: deferred`)

Name the Specs (`specs` in the entry) and ask how they relate:
- **One Thread, several Specs** (`multi_spec`): the parts share a problem and decisions, and ship in order. The usual answer.
- **Separate decisions** (`split`): one part could be parked or rejected on its own. Record `split` and offer `shape-thread`'s Scope check to create the extra Threads and bundle them. Don't split anything yourself.
- **Really just one** (`single`): the extra Specs were drafts that got merged, or are stale.

Write the answer as `scope_decision: <value>` in the Thread's frontmatter. For `multi_spec` with no `planned_specs` yet, add one entry per existing Spec (`key` from the Spec's name, `spec_id`, `depends_on` from what the Specs say), and the `## Planned Specs` table in the body.

### `ask_jury`: no record that the Judge ran

Ask: "When THRD-NNN went through Framing, did the full jury run (Advocate, Skeptic and Judge), and is the transcript still somewhere?"
- **Yes, here it is** (a path, a pasted transcript or an old conversation export): save it as `threads/<thread_id>-verdict.md`, set `verdict_ref` to that path, and add `jury_seats` with one entry per seat that appears in the transcript. Take the models from `jury_models` on the Thread if it has them, otherwise write `model: unknown`. If `inline_verdict` is true, the old verdict text sits in `verdict_ref`: move it into the file.
- **It ran, but the transcript is gone, or I'm not sure:** offer to rerun the jury with `assess-thread` now. It keeps the existing edge-case mapping as a starting point.
- **No, the verdict was written without the jury:** same offer: rerun `assess-thread`.

Never add `jury_seats` for a seat you can't see in a real transcript. If the PM wants to skip a Thread for now, leave it and list it at the end.

5. **Check.** Run `cairn doctor --gaps-json` again, then `cairn check <spec-id>` for each Spec whose Thread changed. Finish with a short summary: what was fixed automatically, what the PM answered, and anything still open with the one thing that would close it.

## What you must not do

- Don't change a Thread's stage or status, or any Spec's content. This skill only records answers and moves existing text into files.
- Don't pick a scope for a Thread with several Specs. The PM decides.
- Don't create a jury record from memory, a summary or a guess.
- Don't commit. Leave the changes for the PM to review, and say which files changed.
