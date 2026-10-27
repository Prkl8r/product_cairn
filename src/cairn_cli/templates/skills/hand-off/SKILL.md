---
name: "hand-off"
description: "Hand a Specified Spec off to engineering: package it with `cairn handoff`, deliver it through the target named in .cairn/config.yaml (an integration such as spec-kit, a custom template, or the team's own script or skill for any SDD process), and record the handoff on the Spec and Thread only once delivery succeeds."
argument-hint: "Spec id, optionally a target name, e.g. SPEC-001 or SPEC-001 zip"
metadata:
  product: cairn
  source: "docs/spec-as-code-revision.md Part 2 (Outputs); cairn handoff"
user-invocable: true
disable-model-invocation: false
---

## What this does

The last step of the core flow. Takes a Spec that passed `check-spec` and sends it where the work gets built. `cairn handoff` owns the package and the record; this skill owns delivery when delivery happens in the agent session (another skill or a subagent). Cairn doesn't assume any particular build process. Targets are named in `.cairn/config.yaml` under `handoff.targets`, and each one names an integration (spec-kit, a custom template, or the team's own in `.cairn/integrations/`) or spells out a skill, subagent or script. A team changes where Specs go without changing the skill.

## Required inputs

1. A Spec id. If the PM didn't give one, use the Spec you're working on in this session and ask a single yes/no to confirm, with a one-line description of what the Spec covers: "Hand off SPEC-NNN (<title>): <one-line summary>?" On a no, ask which Spec. If the PM did give an id, don't ask. Its compile report must say `## Verdict: Pass`, and its Thread must be `Specified` (or the Spec `spec_status: specified` on a multi-Spec Thread). `cairn handoff` checks both; don't re-check by hand.
2. A target name. If the PM didn't give one, run `cairn handoff-targets` and use `default`. If there is no default, show the targets and ask which. If there are no targets at all, set one up first (see below).
3. If several Specs are going, hand them off one at a time, in `depends_on` order.

## Setting up a target

Only when `handoff.targets` is empty, or the PM asks to change where Specs go. Run `cairn handoff-integrations` and ask one question: how does the team turn a Spec into work?
- **spec-kit**: add `speckit: {integration: speckit}`.
- **Our own spec template**: ask for the template's path and where the filled file should go, then add `integration: template` with `template` and `out` (e.g. `docs/specs/{spec_id}.md`).
- **Our own script** (for example, one that fills a template and pushes the spec to another SDD repo): add `kind: script` with `run`. Put anything that varies, such as `repo` or `template`, in the target as its own field and use it in `run` as `{repo}`, `{template}`. If it's reused across repos, write it as `.cairn/integrations/<name>.yaml` with `kind`, `run` and `needs: [repo, ...]`, and have the target name it with `integration:` and set those fields. The script must exit non-zero on failure, since Cairn records the handoff only on exit 0.
- **Another SDD tool with a skill**: add `kind: skill` with that skill and `args`, or `kind: agent` with a subagent and `prompt`.
Show the PM the lines you're adding to `.cairn/config.yaml`, make it the `default` if it's the only one, and carry on.

## Steps

1. **Build the package.** Run `cairn handoff <spec_id> --target <name> --dry-run`. On a non-zero exit, show the error and stop. It names what to fix (status, compile report, unknown target). Read the `WARN` lines and the `Package:` path. Show the PM any `Warning: Spec relies on unverified…` lines: they travel with the Spec and engineering must see them.
2. **Look up the target** in `cairn handoff-targets`. It already has its integration's fields merged in. Fill `{package}`, `{spec}`, `{spec_id}`, `{revision}`, `{thread_id}` and `{root}` in its `args`, `prompt` or `out`.
3. **Deliver, by kind:**
   - `skill`: invoke the named skill with the filled `args`.
   - `agent`: launch the named subagent with the filled `prompt`, and wait for its result.
   - `template`: read the template at `template` and the packaged Spec. Write `out` by filling the template's sections from the Spec only: carry acceptance-criterion ids (`AC-NNN`), slices, out-of-scope items, error and empty states and open questions into whichever sections fit, and cite the Spec id. Leave a section the Spec doesn't cover marked as not covered rather than inventing content. Don't overwrite an existing `out` without asking.
   - `script`: skip this step. `cairn handoff` runs the command in step 4.
4. **Record it**, only if delivery succeeded:
   - `script`: `cairn handoff <spec_id> --target <name>`. This runs the command, filling the target's own fields too, and records the handoff only if the command exits 0. If it fails, show the PM the command's output.
   - other kinds: `cairn handoff <spec_id> --target <name> --delivered`.
   If delivery failed or the PM stopped it, don't record. Say what happened. The Thread stays `Specified`, and the package stays in `.cairn/handoff/<spec_id>/` for a retry.
5. **Report back** in two or three lines: where it went, what the target reports it created, the Thread's status afterwards (it becomes `Handed off` once every planned Spec has gone), and the next step, if the target names one.

## What you must not do

- Do not record a handoff that didn't happen, and never run `--delivered` before delivery finishes.
- Do not edit the Spec or the package to get past a failed check. Point the PM at `check-spec` or `revise-spec`.
- Do not add a requirement to the delivered spec that the Cairn Spec doesn't contain, whatever the target's format asks for.
- Do not change the Thread's `stage`, or set its `status` by hand. `cairn handoff` does that.
- Do not run the target's skill or agent with instructions beyond its `args` or `prompt`.
