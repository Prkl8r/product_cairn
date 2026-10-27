# Handoff integrations

An integration says how a Spec reaches a build process. A target in `.cairn/config.yaml` picks one
with `integration: <name>` and can override any of its fields.

Built in: `speckit`, `template`. Add your own as `.cairn/integrations/<name>.yaml`; a project file
with a built-in's name replaces it.

Fields:

- `description`: one line, shown by `cairn handoff-integrations`.
- `kind`: `skill` (run `skill` with `args`), `agent` (run subagent `agent` with `prompt`),
  `script` (the CLI runs `run`) or `template` (fill `template`, write `out`).
- `expects`: optional path that should exist when the process is set up (e.g. `.specify`). A warning if missing.
- `needs`: optional list of fields the target must set.

`run`, `args`, `prompt` and `out` can use {package}, {spec}, {spec_id}, {revision}, {thread_id} and {root}.

A `script` integration can also use the target's own fields in `run`, so one script serves many
repos. For example, `.cairn/integrations/push-spec.yaml`:

    kind: script
    needs: [repo, template]
    run: "python scripts/push_spec.py --spec {spec} --template {template} --repo {repo}"

and a target: `{integration: push-spec, repo: git@github.com:acme/sdd.git, template: tpl/feature.md}`.
The handoff is recorded only if the script exits 0.
