from __future__ import annotations

import datetime as _dt
import shutil
from importlib import resources
from pathlib import Path
from typing import Optional

import typer
import yaml

from . import __version__

app = typer.Typer(
    name="cairn",
    help="Cairn: install and check the Signal -> Thread -> Spec skill set in a product repo.",
    add_completion=False,
)

SKELETON_DIRS = ["signals", "threads", "specs", "architecture", "library"]

GITIGNORE_ENTRIES = [
    "signals/*/raw/",
    ".env",
    ".env.*",
    ".cairn/inbox.md",
    ".cairn/local/",
]


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
):
    """Install Cairn's skills and skeleton into a product repo."""
    if here and project_name:
        typer.secho("Pass either a project name or --here, not both.", fg=typer.colors.RED)
        raise typer.Exit(1)
    if not here and not project_name:
        typer.secho("Pass a project name, or --here to initialize the current directory.", fg=typer.colors.RED)
        raise typer.Exit(1)

    target = Path.cwd() if here else Path.cwd() / project_name
    target.mkdir(parents=True, exist_ok=True)

    report: list[tuple[str, str]] = []

    # 1. Skills (package-owned, replaced on update unless user has overrides elsewhere)
    templates = _templates_root()
    for skill_dir in sorted((templates / "skills").iterdir()):
        if not skill_dir.is_dir():
            continue
        dst = target / ".claude" / "skills" / skill_dir.name
        status = _copy_if_absent(skill_dir, dst, force)
        report.append((f".claude/skills/{skill_dir.name}/", status))

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

    # 4. .cairn/package.lock (records the installed version)
    cairn_dir = target / ".cairn"
    cairn_dir.mkdir(parents=True, exist_ok=True)
    lock_path = cairn_dir / "package.lock"
    lock_data = {
        "package": "cairn-cli",
        "package_version": __version__,
        "schema_version": 1,
        "skills": _skill_names(),
        "installed_at": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
    }
    lock_path.write_text(yaml.safe_dump(lock_data, sort_keys=False))
    report.append((".cairn/package.lock", "created" if not lock_path.exists() else "updated"))

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
        color = {"created": typer.colors.GREEN, "updated": typer.colors.GREEN,
                 "skipped": typer.colors.YELLOW, "overwritten": typer.colors.CYAN}[status]
        typer.secho(f"  {status:>11}  {path}", fg=color)

    typer.echo()
    typer.echo("Next: fill in charter.yaml, then run onboard-product in Claude Code.")


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

    expected_skills = set(lock_data.get("skills") or _skill_names())
    for skill in sorted(expected_skills):
        skill_file = target / ".claude" / "skills" / skill / "SKILL.md"
        if skill_file.exists():
            typer.secho(f"  OK      .claude/skills/{skill}/SKILL.md", fg=typer.colors.GREEN)
        else:
            typer.secho(f"  MISSING .claude/skills/{skill}/SKILL.md", fg=typer.colors.RED)
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

    if not ok:
        raise typer.Exit(1)
    typer.secho("Cairn install looks healthy.", fg=typer.colors.GREEN)


@app.command()
def version():
    """Print the installed cairn-cli version."""
    typer.echo(__version__)


if __name__ == "__main__":
    app()
