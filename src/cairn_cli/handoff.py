"""Hand a Specified Spec off: build a package (Spec + addendum of supporting artifacts), run the
team's delivery script, then mark the Thread Handed off.

Cairn owns the package; the team owns delivery, in .cairn/handoff.py (installed once by `cairn init`).
"""
from __future__ import annotations

import datetime as _dt
import json
import re
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

import yaml

from . import ledger as _ledger

DESTINATIONS = ("export", "repo", "in_place")
SCRIPT = Path(".cairn") / "handoff.py"
PACKAGES = Path(".cairn") / "handoff"


class HandoffError(Exception):
    """A check failed; nothing was delivered and the Thread is unchanged."""


def compile_verdict(report: Path) -> str | None:
    """'Pass' or 'Fail' from a compile report's verdict line, or None if it has none."""
    if not report.exists():
        return None
    m = re.search(r"verdict:\s*\**\s*(pass|fail)", report.read_text(encoding="utf-8"), re.I)
    return m.group(1).capitalize() if m else None


def repo_id(root: Path) -> str:
    """This repo's remote URL, or its path when it has no remote."""
    try:
        url = subprocess.run(["git", "remote", "get-url", "origin"], cwd=root, capture_output=True,
                             text=True, timeout=10).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        url = ""
    return url or str(root)


def _frontmatter_bounds(text: str) -> tuple[int, int]:
    """Line indexes of the opening and closing '---' of a file's frontmatter."""
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        raise HandoffError("file has no YAML frontmatter")
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return 0, i
    raise HandoffError("frontmatter is not closed with '---'")


def set_keys(text: str, values: dict) -> str:
    """Replace or append top-level frontmatter keys, leaving every other line as written."""
    lines = text.split("\n")
    _, end = _frontmatter_bounds(text)
    head, body = lines[1:end], lines[end:]
    for key, value in values.items():
        out, skipping = [], False
        for line in head:
            if re.match(rf"{re.escape(key)}\s*:", line):
                skipping = True  # drop the key and any indented lines under it
                continue
            if skipping and (line.startswith((" ", "\t", "-")) or not line.strip()):
                continue
            skipping = False
            out.append(line)
        dumped = yaml.safe_dump({key: value}, sort_keys=False, allow_unicode=True, width=1000).rstrip("\n")
        head = out + dumped.split("\n")
    return "\n".join(["---"] + head + body)


def _copy_ref(root: Path, ref: str, dest: Path, notes: list[str], warnings: list[str]) -> None:
    kind, _, target = str(ref).partition(":")
    if not target:
        kind, target = "other", str(ref)
    folder = dest / kind
    if re.match(r"https?://", target):
        try:
            with urllib.request.urlopen(target, timeout=20) as r:
                if "text/html" in r.headers.get("Content-Type", ""):
                    notes.append(f"- `{ref}`: a web page, not a file; open the link")
                    return
                data = r.read()
        except Exception as e:  # unreachable, auth wall, bad URL: list it instead
            notes.append(f"- `{ref}`: could not download ({e.__class__.__name__}); open the link")
            return
        name = Path(target.split("?", 1)[0].rstrip("/")).name or "download"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / name).write_bytes(data)
        _check_api(kind, folder / name, ref, warnings)
        return
    src = (root / target).resolve()
    if not src.exists() and kind == "journey":  # journey:JRN-001 -> journeys/JRN-001.md
        src = (root / "journeys" / f"{target.split('#', 1)[0]}.md").resolve()
    if not src.exists():
        notes.append(f"- `{ref}`: not found in this repo")
        warnings.append(f"{ref} not found; listed in addendum/LINKS.md")
        return
    folder.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        shutil.copytree(src, folder / src.name, dirs_exist_ok=True)
    else:
        shutil.copyfile(src, folder / src.name)
        _check_api(kind, folder / src.name, ref, warnings)


def _check_api(kind: str, path: Path, ref: str, warnings: list[str]) -> None:
    """API specs must be OpenAPI 3.1. Warn, don't block: the PM decides."""
    if kind != "api":
        return
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))  # JSON is valid YAML
    except (yaml.YAMLError, UnicodeDecodeError):
        doc = None
    version = str(doc.get("openapi", "")) if isinstance(doc, dict) else ""
    if not version.startswith("3.1"):
        warnings.append(f"{ref} is not OpenAPI 3.1 (openapi: {version or 'missing'})")


UNVERIFIED_NOTE = ("Warning: Spec relies on unverified {level} Architecture [{system}]. "
                   "Engineering must verify constraints during estimation.")


def unverified_architecture(root: Path, thread: _ledger.Doc) -> list[str]:
    """One warning per system in the Thread's `touches` whose overview isn't a current, verified L2 (C24)."""
    notes = []
    for system in thread.meta.get("touches") or []:
        path = root / "architecture" / str(system) / "overview.md"
        meta = _ledger._split(path)[0] if path.exists() else {}
        level = str(meta.get("readiness") or ("L1" if path.exists() else "L0"))
        if level == "L2" and meta.get("verified") is True:
            if not _expired(meta):
                continue
            level = "L2, past review_ttl"
        notes.append(UNVERIFIED_NOTE.format(level=level, system=system))
    return notes


def _expired(meta: dict) -> bool:
    m = re.fullmatch(r"(\d+)d", str(meta.get("review_ttl") or ""))
    last = meta.get("last_verified")
    if not m or not last:
        return False
    try:
        last = last if isinstance(last, _dt.date) else _dt.date.fromisoformat(str(last))
    except ValueError:
        return False
    return (_dt.date.today() - last).days > int(m.group(1))


def build_package(root: Path, spec: _ledger.Doc, thread: _ledger.Doc) -> tuple[Path, list[str]]:
    """Write .cairn/handoff/<spec-id>/: the Spec with a source link, plus addendum/. Returns (path, warnings)."""
    pkg = root / PACKAGES / spec.id
    if pkg.exists():
        shutil.rmtree(pkg)
    pkg.mkdir(parents=True)
    source = {"repo": repo_id(root), "thread_id": thread.id}
    unverified = unverified_architecture(root, thread)
    keys = {"source": source}
    if unverified:
        keys["unverified_architecture"] = unverified
    (pkg / "spec.md").write_text(set_keys(spec.path.read_text(encoding="utf-8"), keys), encoding="utf-8")

    warnings: list[str] = list(unverified)
    notes: list[str] = []
    refs = [r for r in thread.meta.get("outbound_refs") or [] if not str(r).startswith("spec:")]
    for ref in refs:
        _copy_ref(root, ref, pkg / "addendum", notes, warnings)
    if notes:
        (pkg / "addendum").mkdir(exist_ok=True)
        (pkg / "addendum" / "LINKS.md").write_text(
            "# Supporting artifacts not copied\n\n" + "\n".join(notes) + "\n", encoding="utf-8")
    manifest = {"spec_id": spec.id, "revision": spec.meta.get("revision", 1), "source": source,
                "addendum": refs, "unverified_architecture": unverified, "built_on": _dt.date.today().isoformat()}
    (pkg / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")
    return pkg, warnings


def check(root: Path, spec_id: str, to: str, where: str | None) -> tuple[_ledger.Doc, _ledger.Doc]:
    """Every precondition, before anything is written. Returns (spec, thread)."""
    if to not in DESTINATIONS:
        raise HandoffError(f"--to must be one of: {', '.join(DESTINATIONS)}")
    if to != "in_place" and not where:
        raise HandoffError(f"--to {to} needs --where (the team, or the target repo's local checkout)")
    docs = _ledger.load(root)
    spec = docs.get(spec_id)
    if not spec or spec.kind != "spec":
        raise HandoffError(f"no Spec with id {spec_id} under specs/")
    thread = docs.get(str(spec.meta.get("thread_id", "")))
    if not thread or thread.kind != "thread":
        raise HandoffError(f"{spec_id} has no parent Thread (thread_id: {spec.meta.get('thread_id')})")
    status = _ledger.stage_status(thread.meta)[1]
    if status != "Specified":
        raise HandoffError(f"{thread.id} is {status}, not Specified. Set status: Specified once the Spec "
                           "compiles clean, then hand off.")
    verdict = compile_verdict(spec.path.with_name(f"{spec_id}.compile_report.md"))
    if verdict != "Pass":
        raise HandoffError(f"{spec_id}'s compile report " + ("is missing" if verdict is None else "says Fail")
                           + ". Run check-spec first.")
    return spec, thread


def run_script(root: Path, pkg: Path, to: str, where: str | None) -> None:
    script = root / SCRIPT
    if not script.exists():
        if to == "in_place":
            return  # nothing to deliver
        raise HandoffError(f"{SCRIPT} is missing. Run `cairn init --here` to install the template.")
    r = subprocess.run([sys.executable, str(script), "--package", str(pkg), "--to", to, "--where", where or ""],
                       cwd=root)
    if r.returncode:
        raise HandoffError(f"{SCRIPT} exited with code {r.returncode}; the Thread was not marked Handed off.")


def mark_handed_off(thread: _ledger.Doc, spec: _ledger.Doc, to: str, where: str | None) -> None:
    record = {"to": to}
    if where:
        record["where"] = where
    record.update({"on": _dt.date.today().isoformat(), "spec_id": spec.id,
                   "revision": spec.meta.get("revision", 1)})
    text = thread.path.read_text(encoding="utf-8")
    thread.path.write_text(set_keys(text, {"status": "Handed off", "handoff": record}), encoding="utf-8")
