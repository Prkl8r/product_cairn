from __future__ import annotations

import datetime as _dt
import json
import shutil
import stat
import subprocess
import sys
from importlib import resources
from pathlib import Path
from typing import Optional

import typer
import yaml

from . import __version__
from . import handoff as _handoff
from . import jury as _jury
from . import ledger as _ledger

app = typer.Typer(
    name="cairn",
    help="Cairn: install and check the signal -> Thread -> Spec skill set in a product repo.",
    add_completion=False,
)

SKELETON_DIRS = ["signals", "threads", "specs", "journeys", "architecture", "library"]

GITIGNORE_ENTRIES = [
    "signals/*/raw/",
    ".env",
    ".env.*",
    ".cairn/inbox.md",
    ".cairn/local/",
    ".cairn/handoff/",
]

# Skills renamed in a later release: old folder name -> new name. `cairn init --force`
# removes the old folders so a repo doesn't list both.
RETIRED_SKILLS = {
    "spec-generator": "draft-spec",
    "compile-check": "check-spec",
    "onboard-product": "onboard",
}


# Where each supported agent looks for project skills (all read the Agent Skills SKILL.md format).
# VS Code covers Copilot agent mode, including Ollama models picked through it. Cursor also reads
# .agents/skills/, so installing both codex and cursor shows each skill twice there.
AGENT_SKILL_DIRS = {
    "claude": Path(".claude/skills"),
    "vscode": Path(".github/skills"),
    "codex": Path(".agents/skills"),
    "cursor": Path(".cursor/skills"),
    "cline": Path(".cline/skills"),
}
CLAUDE_AGENTS_DIR = Path(".claude/agents")
CONFIG_FILE = Path(".cairn/config.yaml")
AGENT_LABELS = {
    "claude": "Claude Code",
    "vscode": "VS Code / Copilot",
    "codex": "Codex CLI",
    "cursor": "Cursor",
    "cline": "Cline",
}


def _check_agents(agents: list[str]) -> list[str]:
    unknown = [a for a in agents if a not in AGENT_SKILL_DIRS]
    if unknown:
        typer.secho(f"Unknown --agent {', '.join(unknown)}. Choose from: {', '.join(AGENT_SKILL_DIRS)}.", fg=typer.colors.RED)
        raise typer.Exit(1)
    return sorted(set(agents), key=list(AGENT_SKILL_DIRS).index)


def _locked_agents(target: Path) -> list[str]:
    lock_path = target / ".cairn" / "package.lock"
    if not lock_path.exists():
        return []
    return (yaml.safe_load(lock_path.read_text()) or {}).get("agents") or ["claude"]


def _pick_agents(preselected: list[str]) -> list[str]:
    """Checkbox menu of agents. Falls back to claude when there's no terminal to ask on."""
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        return preselected or ["claude"]
    import questionary

    width = max(len(l) for l in AGENT_LABELS.values())
    choices = [
        questionary.Choice(f"{AGENT_LABELS[a]:<{width}}  {d}/", value=a, checked=a in (preselected or ["claude"]))
        for a, d in AGENT_SKILL_DIRS.items()
    ]
    picked = questionary.checkbox(
        "Which agents should Cairn install skills for?",
        choices=choices,
        instruction="(space to toggle, enter to confirm)",
        validate=lambda xs: bool(xs) or "Pick at least one.",
    ).ask()
    if picked is None:  # Ctrl-C
        raise typer.Exit(1)
    return picked


def _templates_root() -> Path:
    return Path(resources.files("cairn_cli") / "templates")


def _skill_names() -> list[str]:
    skills_dir = _templates_root() / "skills"
    return sorted(p.name for p in skills_dir.iterdir() if p.is_dir())


def _copy_if_absent(src: Path, dst: Path, force: bool) -> str:
    """Copy src to dst unless dst already exists. Returns 'created', 'skipped', or 'overwritten'."""
    if dst.exists() and not force:
        return "skipped"
    status = "overwritten" if dst.exists() else "created"
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
    else:
        shutil.copyfile(src, dst)
    return status


STATUS_HOOK_MARKER = "# cairn: refresh STATUS.md/STATUS.json"
STATUS_HOOK = f"""{STATUS_HOOK_MARKER}
if command -v cairn >/dev/null 2>&1; then
  cairn snapshot >/dev/null && git add STATUS.md STATUS.json
fi
"""


def _install_status_hook(target: Path) -> tuple[str, str]:
    """Add the snapshot step to pre-commit, keeping any hook already there. Honors core.hooksPath."""
    try:
        hooks = subprocess.run(["git", "rev-parse", "--git-path", "hooks"], cwd=target,
                               capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return ("pre-commit hook", "not a git repo")
    hook = (target / hooks / "pre-commit").resolve()
    label = f"{hook.relative_to(target) if hook.is_relative_to(target) else hook}"
    existing = hook.read_text() if hook.exists() else ""
    if STATUS_HOOK_MARKER in existing:
        return (label, "skipped")
    hook.parent.mkdir(parents=True, exist_ok=True)
    if existing:
        hook.write_text(existing.rstrip("\n") + "\n\n" + STATUS_HOOK)
    else:
        hook.write_text("#!/bin/sh\n" + STATUS_HOOK)
    hook.chmod(hook.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return (label, "updated" if existing else "created")


@app.command()
def init(
    project_name: Optional[str] = typer.Argument(
        None, help="Directory to create and initialize. Omit when using --here."
    ),
    here: bool = typer.Option(
        False, "--here", help="Initialize in the current directory instead of creating a new one."
    ),
    force: bool = typer.Option(
        False, "--force", help="Overwrite package-owned files that already exist (skills, templates). Never touches charter.yaml, signals/, threads/, or specs/ content."
    ),
    status_hook: bool = typer.Option(
        False, "--status-hook", help="Add a git pre-commit hook that refreshes STATUS.md/STATUS.json on every commit. Safe to run on an existing install."
    ),
    skills_only: bool = typer.Option(
        False, "--skills-only", help="Install or refresh the skills folder only: no skeleton, charter, lock file, or .gitignore changes."
    ),
    agent: Optional[list[str]] = typer.Option(
        None, "--agent", help=f"Agent to install skills for; repeat for several. One of: {', '.join(AGENT_SKILL_DIRS)}. "
        "Omit to choose from a menu (defaults to claude when not run in a terminal)."
    ),
):
    """Install Cairn's skills and skeleton into a product repo."""
    if here and project_name:
        typer.secho("Pass either a project name or --here, not both.", fg=typer.colors.RED)
        raise typer.Exit(1)
    if not here and not project_name:
        typer.secho("Pass a project name, or --here to initialize the current directory.", fg=typer.colors.RED)
        raise typer.Exit(1)

    target = Path.cwd() if here else Path.cwd() / project_name
    agents = _check_agents(agent) if agent else _pick_agents(_locked_agents(target))
    target.mkdir(parents=True, exist_ok=True)

    report: list[tuple[str, str]] = []

    # 1. Skills (package-owned, replaced on update unless user has overrides elsewhere)
    templates = _templates_root()
    for name in agents:
        skills_rel = AGENT_SKILL_DIRS[name]
        for skill_dir in sorted((templates / "skills").iterdir()):
            if not skill_dir.is_dir():
                continue
            dst = target / skills_rel / skill_dir.name
            status = _copy_if_absent(skill_dir, dst, force)
            report.append((f"{skills_rel}/{skill_dir.name}/", status))
        # Jury seats: real subagents for Claude Code, reference files for jury-duty's inline mode everywhere.
        for seat in sorted((templates / "agents").glob("*.md")):
            dst = target / skills_rel / "jury-duty" / "seats" / seat.name
            _copy_if_absent(seat, dst, force=True)
            if name == "claude":
                dst = target / CLAUDE_AGENTS_DIR / seat.name
                report.append((f"{CLAUDE_AGENTS_DIR}/{seat.name}", _copy_if_absent(seat, dst, force)))
        for old, new in RETIRED_SKILLS.items():
            old_dst = target / skills_rel / old
            if not old_dst.exists():
                continue
            if force:
                shutil.rmtree(old_dst)
                report.append((f"{skills_rel}/{old}/ (now {new})", "removed"))
            else:
                report.append((f"{skills_rel}/{old}/ (now {new}; --force removes it)", "retired"))

    if skills_only:
        for path, status in report:
            typer.echo(f"  {status:>11}  {path}")
        return

    # 2. Skeleton directories (user-owned content, we just make sure the folder exists)
    for name in SKELETON_DIRS:
        d = target / name
        existed = d.exists()
        d.mkdir(parents=True, exist_ok=True)
        keep = d / ".gitkeep"
        if not any(d.iterdir()):
            keep.touch()
        report.append((f"{name}/", "skipped" if existed else "created"))

    # 3. charter.yaml (user-owned, never overwritten)
    charter_dst = target / "charter.yaml"
    status = _copy_if_absent(templates / "charter.yaml", charter_dst, force=False)
    report.append(("charter.yaml", status))

    # 3b. checklist.md (user-owned, never overwritten)
    checklist_dst = target / "checklist.md"
    status = _copy_if_absent(templates / "checklist.md", checklist_dst, force=False)
    report.append(("checklist.md", status))

    # 3c. .cairn/handoff.py (user-owned delivery script, never overwritten)
    status = _copy_if_absent(templates / "handoff.py", target / _handoff.SCRIPT, force=False)
    report.append((str(_handoff.SCRIPT), status))

    # 3d. .cairn/config.yaml (user-owned project settings, never overwritten)
    status = _copy_if_absent(templates / "config.yaml", target / CONFIG_FILE, force=False)
    report.append((str(CONFIG_FILE), status))

    # 4. .cairn/package.lock (records the installed version)
    cairn_dir = target / ".cairn"
    cairn_dir.mkdir(parents=True, exist_ok=True)
    lock_path = cairn_dir / "package.lock"
    locked = _check_agents(_locked_agents(target) + agents)
    lock_data = {
        "package": "cairn-cli",
        "package_version": __version__,
        "schema_version": 1,
        "skills": _skill_names(),
        "agents": locked,
        "installed_at": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
    }
    lock_path.write_text(yaml.safe_dump(lock_data, sort_keys=False))
    report.append((".cairn/package.lock", "created" if not lock_path.exists() else "updated"))

    # 4b. Optional pre-commit hook that keeps STATUS.md/STATUS.json current
    if status_hook:
        report.append(_install_status_hook(target))

    # 5. .gitignore entries (append, don't duplicate, don't clobber the rest of the file)
    gitignore = target / ".gitignore"
    existing = gitignore.read_text().splitlines() if gitignore.exists() else []
    missing = [e for e in GITIGNORE_ENTRIES if e not in existing]
    if missing:
        with gitignore.open("a") as f:
            if existing and existing[-1] != "":
                f.write("\n")
            f.write("# cairn\n")
            for entry in missing:
                f.write(entry + "\n")
    report.append((".gitignore", "updated" if missing else "skipped"))

    typer.secho(f"Cairn {__version__} installed into {target}", fg=typer.colors.GREEN)
    for path, status in report:
        color = {"created": typer.colors.GREEN, "updated": typer.colors.GREEN, "skipped": typer.colors.YELLOW,
                 "overwritten": typer.colors.CYAN,
                 "removed": typer.colors.CYAN, "retired": typer.colors.YELLOW, "not a git repo": typer.colors.RED}[status]
        typer.secho(f"  {status:>11}  {path}", fg=color)

    typer.echo()
    typer.echo(f"Next: fill in charter.yaml, then run onboard in {', '.join(AGENT_LABELS[a] for a in agents)}.")


@app.command()
def doctor(
    path: Path = typer.Argument(Path("."), help="Product repo to check. Defaults to the current directory."),
):
    """Check that a product repo's Cairn install is complete and consistent."""
    target = path.resolve()
    ok = True

    lock_path = target / ".cairn" / "package.lock"
    if not lock_path.exists():
        typer.secho("MISSING  .cairn/package.lock — this repo has not run `cairn init`.", fg=typer.colors.RED)
        raise typer.Exit(1)

    lock_data = yaml.safe_load(lock_path.read_text()) or {}
    typer.echo(f"Installed package version: {lock_data.get('package_version', 'unknown')}")
    if lock_data.get("package_version") != __version__:
        typer.secho(
            f"  note: installed CLI is {__version__}, repo was initialized with {lock_data.get('package_version')}. Run `cairn init --force` to update skills.",
            fg=typer.colors.YELLOW,
        )

    expected_skills = set(lock_data.get("skills") or _skill_names()) - set(RETIRED_SKILLS)
    for old, new in RETIRED_SKILLS.items():
        if old in (lock_data.get("skills") or []):
            expected_skills.add(new)
    for agent in lock_data.get("agents") or ["claude"]:
        skills_rel = AGENT_SKILL_DIRS.get(agent)
        if skills_rel is None:
            typer.secho(f"  WARN    package.lock lists unknown agent {agent!r}", fg=typer.colors.YELLOW)
            continue
        flag = f" --agent {agent}"
        for old, new in RETIRED_SKILLS.items():
            if (target / skills_rel / old).exists():
                typer.secho(f"  WARN    {skills_rel}/{old}/ was renamed to {new}. "
                            f"Run `cairn init --here --force{flag}` to replace it.", fg=typer.colors.YELLOW)
        for skill in sorted(expected_skills):
            skill_file = target / skills_rel / skill / "SKILL.md"
            template = _templates_root() / "skills" / skill / "SKILL.md"
            if skill_file.exists() and template.exists() and skill_file.read_bytes() != template.read_bytes():
                typer.secho(f"  WARN    {skills_rel}/{skill}/SKILL.md differs from the installed CLI's copy. "
                            f"Run `cairn init --here --force{flag}` to update it.", fg=typer.colors.YELLOW)
            elif skill_file.exists():
                typer.secho(f"  OK      {skills_rel}/{skill}/SKILL.md", fg=typer.colors.GREEN)
            else:
                typer.secho(f"  MISSING {skills_rel}/{skill}/SKILL.md", fg=typer.colors.RED)
                ok = False

    charter_path = target / "charter.yaml"
    if not charter_path.exists():
        typer.secho("  MISSING charter.yaml", fg=typer.colors.RED)
        ok = False
    else:
        charter = yaml.safe_load(charter_path.read_text()) or {}
        tbd_fields = [k for k, v in charter.items() if isinstance(v, str) and v.strip().upper() == "TBD"]
        if tbd_fields:
            typer.secho(f"  WARN    charter.yaml has unfilled fields: {', '.join(tbd_fields)}", fg=typer.colors.YELLOW)
        else:
            typer.secho("  OK      charter.yaml", fg=typer.colors.GREEN)

    for name in SKELETON_DIRS:
        d = target / name
        if d.is_dir():
            typer.secho(f"  OK      {name}/", fg=typer.colors.GREEN)
        else:
            typer.secho(f"  MISSING {name}/", fg=typer.colors.RED)
            ok = False

    if (target / _handoff.SCRIPT).exists():
        typer.secho(f"  OK      {_handoff.SCRIPT}", fg=typer.colors.GREEN)
    else:
        typer.secho(f"  WARN    {_handoff.SCRIPT} missing; `cairn handoff` can't deliver. Run `cairn init --here`.",
                    fg=typer.colors.YELLOW)

    config_path = target / CONFIG_FILE
    if config_path.exists():
        result = _jury.draw(_jury.settings(config_path), seed=0)
        warnings = result["warnings"]
        if not warnings and result["draw"] == "config" and (result["advocate"], result["skeptic"]) == ("opus", "sonnet"):
            warnings = ["the Advocate and Skeptic are pinned to opus/sonnet (the pre-0.4 defaults), so the coin "
                        "flip never runs. Blank them under jury.models to use it, or set jury.draw: fixed to keep this."]
        if warnings:
            typer.secho(f"  WARN    {CONFIG_FILE}: {warnings[0]}", fg=typer.colors.YELLOW)
        else:
            typer.secho(f"  OK      {CONFIG_FILE}", fg=typer.colors.GREEN)
    else:
        typer.secho(f"  WARN    {CONFIG_FILE} missing; the jury uses its default models. Run `cairn init --here`.",
                    fg=typer.colors.YELLOW)

    for d in _ledger.load(target).values():
        if d.broken:
            typer.secho(f"  WARN    {d.id} references missing files: {', '.join(d.broken)}", fg=typer.colors.YELLOW)

    if not ok:
        raise typer.Exit(1)
    typer.secho("Cairn install looks healthy.", fg=typer.colors.GREEN)


PATH_OPT = typer.Option(Path("."), "--path", help="Product repo. Defaults to the current directory.")
JSON_OPT = typer.Option(False, "--json", help="Machine-readable output for scripts and other tools. Hides restricted items.")
RESTRICTED_OPT = typer.Option(False, "--include-restricted", help="Include data_class: restricted items in --json/snapshot output.")


@app.command()
def ledger(path: Path = PATH_OPT, as_json: bool = JSON_OPT, include_restricted: bool = RESTRICTED_OPT):
    """What has been asked of the product, and what has gone to engineering."""
    root = path.resolve()
    docs = _ledger.load(root)
    if as_json:
        typer.echo(json.dumps(_ledger.snapshot(_ledger.visible(docs, include_restricted), root), default=str))
        return

    signals = [d for d in docs.values() if d.kind == "signal"]
    threads = [d for d in docs.values() if d.kind == "thread"]
    specs = [d for d in docs.values() if d.kind == "spec"]
    sent = _ledger.sent(docs)
    lock = lambda d: " [restricted]" if d.restricted else ""

    typer.secho(f"Asked — {len(signals)} signals", bold=True)
    for s in signals:
        typer.echo(f"  {s.id:<16} {str(s.meta.get('type', '?')):<12} {_ledger.thread_state(s, docs):<14} "
                   f"{s.updated}  {_ledger.snippet(s, 50)}{lock(s)}")

    typer.secho(f"\nThreads — {len(threads)}", bold=True)
    for t in threads:
        sig = ", ".join(sorted(l for l in t.links if docs[l].kind == "signal")) or "-"
        typer.echo(f"  {t.id:<16} {_ledger.thread_label(t.meta):<22} {t.updated}  signals: {sig}{lock(t)}")

    typer.secho("\nSent to engineering", bold=True)
    for s in sent:
        t = next(docs[l] for l in s.links if docs[l].kind == "thread")
        line = f"  {s.id:<16} rev {s.meta.get('revision', 1):<3} {t.id} {s.updated}"
        kb = _ledger.last_kickback(t.meta, s.id)
        if kb:
            line += f"  last kickback: {kb.get('category') or 'pm'}"
        typer.echo(line)
    if not sent:
        typer.echo("  nothing yet")
    if len(specs) > len(sent):
        typer.echo(f"  ({len(specs) - len(sent)} spec(s) drafted, not yet handed off)")

    refs = [d for d in docs.values() if d.kind in _ledger.REFERENCE_KINDS]
    if refs:
        typer.secho(f"\nReference — {len(refs)} library/architecture docs (cairn find --kind library|architecture)", bold=True)

    broken = [d for d in docs.values() if d.broken]
    if broken:
        typer.secho("\nBroken references — these point at files that don't exist", bold=True, fg=typer.colors.RED)
        for d in broken:
            typer.secho(f"  {d.id:<16} {', '.join(d.broken)}", fg=typer.colors.RED)


@app.command()
def find(
    query: str = typer.Argument(..., help="Words to search for, or an exact id to show everything linked to it."),
    kind: Optional[str] = typer.Option(None, "--kind", help="Limit to signal, thread, spec, journey, library, or architecture."),
    path: Path = PATH_OPT,
    as_json: bool = JSON_OPT,
    include_restricted: bool = RESTRICTED_OPT,
):
    """Search signals, threads, specs, and reference docs. An exact id shows everything linked to it."""
    root = path.resolve()
    docs = _ledger.load(root)
    if as_json:
        docs = _ledger.visible(docs, include_restricted)
    exact = query in docs
    found = _ledger.lineage(docs, query) if exact else [d for _, d in _ledger.search(docs, query, kind)]
    if as_json:
        typer.echo(json.dumps({"query": query, "lineage": exact,
                               "results": [_ledger.as_dict(d, docs, root) for d in found]}, default=str))
        if not found:
            raise typer.Exit(1)
        return
    if not found:
        typer.echo("No matches.")
        raise typer.Exit(1)
    for d in found:
        tail = d.path.relative_to(root) if exact else _ledger.snippet(d, 60)
        typer.echo(f"{d.kind:<12} {d.id:<24} {_ledger.thread_state(d, docs):<12} {d.updated}  {tail}")


@app.command()
def snapshot(path: Path = PATH_OPT, include_restricted: bool = RESTRICTED_OPT):
    """Write STATUS.json and STATUS.md at the repo root, so anyone can check status without installing Cairn."""
    root = path.resolve()
    docs = _ledger.visible(_ledger.load(root), include_restricted)
    snap = _ledger.snapshot(docs, root)
    (root / "STATUS.json").write_text(json.dumps(snap, indent=1, default=str) + "\n")
    (root / "STATUS.md").write_text(_ledger.status_markdown(snap))
    typer.echo(f"Wrote STATUS.json and STATUS.md ({len(snap['threads'])} threads, {len(snap['signals'])} signals).")
    if snap["broken_refs"]:
        typer.secho(f"  {len(snap['broken_refs'])} file(s) have broken references — see STATUS.md", fg=typer.colors.YELLOW)


@app.command()
def handoff(
    spec_id: str = typer.Argument(..., help="The Spec to hand off, e.g. SPEC-001."),
    to: Optional[str] = typer.Option(None, "--to", help="export (to a team), repo (to another repo), or in_place (spec-kit picks it up here)."),
    where: Optional[str] = typer.Option(None, "--where", help="The team, or the target repo's local checkout. Not needed for in_place."),
    target: Optional[str] = typer.Option(None, "--target", help="A named target from handoff.targets in .cairn/config.yaml, in place of --to. 'default' uses handoff.default."),
    delivered: bool = typer.Option(False, "--delivered", help="With --target: the hand-off skill already delivered it; only record the handoff."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Build the package only: don't run the delivery script or change the Thread."),
    path: Path = PATH_OPT,
):
    """Hand a Spec off: package it with its supporting artifacts, deliver it, and record it on the Spec and Thread."""
    root = path.resolve()
    try:
        if (to is None) == (target is None):
            raise _handoff.HandoffError("give exactly one of --to or --target")
        if delivered and target is None:
            raise _handoff.HandoffError("--delivered goes with --target")
        kind = None
        if target is not None:
            target, conf = _handoff.load_target(root, None if target == "default" else target)
            kind = conf["kind"]
            if kind in _handoff.AGENT_KINDS and not (dry_run or delivered):
                raise _handoff.HandoffError(
                    f"target '{target}' ({kind}) is delivered by the hand-off skill: build with --dry-run, "
                    "deliver it, then record with --delivered")
            spec, thread = _handoff.check(root, spec_id, "in_place", None)
        else:
            spec, thread = _handoff.check(root, spec_id, to, where)
        pkg, warnings = _handoff.build_package(root, spec, thread)
        if target is not None:
            warnings += _handoff.target_warnings(root, conf)
        for w in warnings:
            typer.secho(f"  WARN  {w}", fg=typer.colors.YELLOW)
        typer.echo(f"Package: {pkg.relative_to(root)}")
        if target is not None:
            typer.echo(f"Target: {target} ({kind})")
        if dry_run:
            typer.echo("Dry run: nothing delivered, Thread unchanged.")
            return
        if target is None:
            _handoff.run_script(root, pkg, to, where)
            thread_status = _handoff.mark_handed_off(root, thread, spec, to, where)
        else:
            if kind == "script" and not delivered:
                _handoff.run_target_script(root, conf, _handoff.placeholders(root, pkg, spec, thread))
            thread_status = _handoff.mark_handed_off(root, thread, spec, target, None, kind)
    except _handoff.HandoffError as e:
        typer.secho(str(e), fg=typer.colors.RED)
        raise typer.Exit(1)
    dest = target if target is not None else to
    sent = f"{spec.id} -> {dest}{' ' + where if where and target is None else ''}"
    if thread_status == "Handed off":
        typer.secho(f"{thread.id} is Handed off ({sent}).", fg=typer.colors.GREEN)
    else:
        pending = [s or "(not drafted)" for s in _handoff.thread_spec_ids(thread) if s != spec.id]
        typer.secho(f"Handed off {sent}. {thread.id} stays {thread_status}; still to go: {', '.join(pending)}.",
                    fg=typer.colors.GREEN)


@app.command("handoff-targets")
def handoff_targets(path: Path = PATH_OPT):
    """List the named handoff targets in .cairn/config.yaml, merged with their integrations, as JSON, for the hand-off skill."""
    root = path.resolve()
    conf = _handoff.targets(root)
    out = {}
    for name, t in (conf.get("targets") or {}).items():
        try:
            out[name] = _handoff.resolve(root, name, t)
        except _handoff.HandoffError as e:
            out[name] = {"error": str(e)}
    typer.echo(json.dumps({"default": conf.get("default"), "targets": out}, indent=1))


@app.command("handoff-integrations")
def handoff_integrations(path: Path = PATH_OPT):
    """List the handoff integrations a target can name: built in, plus .cairn/integrations/."""
    for name, i in _handoff.integrations(path.resolve()).items():
        typer.echo(f"{name:12} {i.get('kind', '?'):9} {i.get('description', '')}")


@app.command("jury-draw")
def jury_draw(
    seed: Optional[int] = typer.Option(None, "--seed", help="Repeat an earlier draw (the seed is in its output)."),
    path: Path = PATH_OPT,
):
    """Pick the jury's models: the Judge is fixed, a coin flip decides which debater gets which model."""
    result = _jury.draw(_jury.settings(path.resolve() / CONFIG_FILE), seed)
    typer.echo(json.dumps(result))


@app.command()
def version():
    """Print the installed cairn-cli version."""
    typer.echo(__version__)


if __name__ == "__main__":
    app()
