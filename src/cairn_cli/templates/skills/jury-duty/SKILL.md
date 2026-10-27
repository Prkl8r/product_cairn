---
name: "jury-duty"
description: "Run the Advocate/Skeptic/Judge critique on a Thread: three rounds of debate, then a verdict listing the concrete edge cases, each mapped to a criterion or deferred. Called by assess-thread; also usable on its own to pressure-test a Thread or a draft."
argument-hint: "thread id (or a path to a draft to pressure-test)"
metadata:
  product: cairn
  source: "docs/spec-as-code-revision.md Part 1 section 8 (Trust Model, Jury)"
user-invocable: true
disable-model-invocation: false
---

## What this does

The one place the jury critique is defined. `assess-thread` calls it for the Framing-stage verdict. A PM can also run it on its own to pressure-test a Thread or a draft at any point; on its own it only reports and writes nothing to the Thread.

## Required inputs

1. The Thread file (or the draft the PM pointed at).
2. `charter.yaml`.
3. Every signal file the Thread references, and every `architecture/<system>/overview.md` for systems in `touches`.
4. `.cairn/config.yaml`, if it exists: `jury.draw`, `jury.debate_models` and `jury.models` decide each seat's model (read through `cairn jury-draw`, below).

Collect these as **paths**. The jurors read the files themselves.

## How to run it

### Claude Code: separate agents

Use the `jury-advocate`, `jury-skeptic` and `jury-judge` agents (namespaced `cairn:` when Cairn is installed as a plugin). The Advocate and Skeptic run on different models; that separation is the point of the jury.

**Models:** before round 1, run `cairn jury-draw` once and use its result for the whole jury. It prints JSON like `{"advocate": "sonnet", "skeptic": "opus", "judge": "opus", "draw": "coin", "seed": 41723, "warnings": []}`. Pass each seat's model as the model override on every call to that agent. Never pick or flip the models yourself: the draw has to come from the script so it's actually random. The Judge stays on one model while a coin flip decides which debater gets which model, so the Judge shares a model with the Advocate half the time and with the Skeptic the other half, and the stronger model doesn't always argue for the proposal. Seats pinned under `jury.models` skip the draw, and `jury.draw: fixed` turns it off.

If `cairn` isn't installed, say so and use the agent files' defaults (Advocate `opus`, Skeptic `sonnet`, Judge `opus`), recording `draw: fixed`. If the result has a warning (Advocate and Skeptic on the same model), show it to the PM before round 1 and record `jury_mode: agents (same model)` in place of `agents`.

1. **Round 1:** run `jury-advocate` and `jury-skeptic` in parallel, each given only the input paths. Neither sees the other's opening.
2. **Round 2:** give `jury-advocate` the Skeptic's round-1 output; then give `jury-skeptic` the Advocate's round-2 responses.
3. **Round 3:** repeat round 2 once more.
4. **Verdict:** give `jury-judge` the input paths and all six outputs, verbatim.

Pass outputs between jurors verbatim; don't summarize or soften them. If a juror's output breaks its format or word cap, rerun that call once, then use what you have.

### Other agents (VS Code, Codex, Cursor, Cline): inline

No separate agents are available. Play the three seats in turn in this conversation, using the same rules and output formats as the agent files (`seats/jury-*.md` beside this file; `cairn init` puts them there), and in the same round order. Before any round 2 response, write the Skeptic's round-1 cases in full first, so the Advocate answers what was actually said. State in the verdict: `jury_mode: inline (single model)` — the Skeptic did not run on a separate model, so the critique is weaker.

## Output

Show the PM the Judge's verdict, not the transcript: the verdict line, the summary, the standing edge cases with their mapping or deferral, what was dismissed and why, and any unverified overviews. Offer the full round-by-round transcript if they want it.

Return to the caller (`assess-thread`) the Judge's YAML as-is, plus `jury_mode: agents | agents (same model) | inline` and the model each seat ran on, with how they were chosen (`jury_models: {advocate, skeptic, judge, draw, seed}`). Recording the draw lets the PM check later whether verdicts follow whichever side drew the stronger model.

Also return the full transcript, each seat's output verbatim under a heading per call (`### Round 1: Advocate`, …, `### Verdict: Judge`), and `jury_seats`: one entry per seat that actually ran, with the model it ran on and how many calls it made:

```yaml
jury_seats:
  - {seat: advocate, model: sonnet, calls: 3}
  - {seat: skeptic, model: opus, calls: 3}
  - {seat: judge, model: opus, calls: 1}
```

Inline, write `model: inline` for each seat. List only seats that produced output. If the Judge call failed or was skipped, there is no verdict: say so and stop. Never write the verdict yourself in its place.

## What you must not do

- Do not write to the Thread, Spec or any file. The caller records the verdict.
- Do not merge the seats into one pass in agents mode. Single-pass critique belongs to `fast-track` only.
- Do not drop or reword a standing edge case between the Judge's output and the PM.
