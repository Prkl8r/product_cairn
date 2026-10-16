"""Delivery step for `cairn handoff`. Yours to edit: `cairn init` installs it once and never overwrites it.

Cairn has already built the package before calling this:

    <package>/spec.md          the Spec, with a `source` link back to this repo and its Thread
    <package>/addendum/        copies of the Thread's supporting artifacts (mocks, OpenAPI 3.1 files, ...)
    <package>/manifest.json    spec_id, revision, source, what went into the addendum

Exit non-zero to stop: the Thread then stays Specified.
"""
import argparse
import shutil
import sys
from pathlib import Path


def export(package: Path, where: str) -> None:
    """Zip the package for a team. Replace with an upload, an email, a ticket attachment, ..."""
    archive = shutil.make_archive(str(package), "zip", package)
    print(f"Wrote {archive} for {where}.")


def repo(package: Path, where: str) -> None:
    """Copy into a local checkout of the target repo, where spec-kit expects specs/<id>/spec.md."""
    target_root = Path(where).expanduser()
    if not (target_root / ".git").exists():
        sys.exit(f"{where} is not a local git checkout. Clone the target repo and pass its path to --where.")
    dest = target_root / "specs" / package.name
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(package, dest)
    print(f"Copied to {dest}. Commit it in that repo.")


def in_place(package: Path, where: str) -> None:
    """The Spec stays where it is for spec-kit to pick up. Nothing to deliver."""


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--package", type=Path, required=True)
    p.add_argument("--to", choices=["export", "repo", "in_place"], required=True)
    p.add_argument("--where", default="")
    a = p.parse_args()
    {"export": export, "repo": repo, "in_place": in_place}[a.to](a.package, a.where)
