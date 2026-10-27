import json
import subprocess

import pytest
import yaml
from typer.testing import CliRunner

from cairn_cli import handoff as h
from cairn_cli.cli import app

runner = CliRunner()

THREAD = """---
thread_id: THRD-001
stage: Validating
status: {status}
owner: pm
inbound_refs: ["idea:IDEA-001"]
outbound_refs:
  - spec:SPEC-001
  - api:design/api.yaml
  - mock:design/screens
  - mock:design/missing.png
---

Body stays put.
"""

SPEC = """---
spec_id: SPEC-001
thread_id: THRD-001
revision: 2
---

Spec body.
"""


def frontmatter(path):
    return yaml.safe_load(path.read_text().split("---")[1])


@pytest.fixture
def repo(tmp_path):
    for d in ("signals/idea", "threads", "specs", "design/screens"):
        (tmp_path / d).mkdir(parents=True)
    (tmp_path / "signals/idea/IDEA-001.md").write_text("---\nsignal_id: IDEA-001\ntype: idea\n---\nAn idea.\n")
    (tmp_path / "threads/THRD-001.md").write_text(THREAD.format(status="Specified"))
    (tmp_path / "specs/SPEC-001.md").write_text(SPEC)
    (tmp_path / "specs/SPEC-001.compile_report.md").write_text("# Report\n\n## Verdict: **Pass**\n")
    (tmp_path / "design/api.yaml").write_text("openapi: 3.1.0\ninfo: {title: t, version: '1'}\n")
    (tmp_path / "design/screens/home.png").write_bytes(b"png")
    return tmp_path


def run(repo, *args):
    return runner.invoke(app, ["handoff", *args, "--path", str(repo)])


def install_script(repo):
    (repo / ".cairn").mkdir(exist_ok=True)
    src = h.Path(h.__file__).parent / "templates" / "handoff.py"
    (repo / h.SCRIPT).write_text(src.read_text())


def test_export_builds_package_and_marks_thread(repo):
    install_script(repo)
    r = run(repo, "SPEC-001", "--to", "export", "--where", "platform team")
    assert r.exit_code == 0, r.output
    pkg = repo / ".cairn/handoff/SPEC-001"
    spec = frontmatter(pkg / "spec.md")
    assert spec["source"] == {"repo": str(repo), "thread_id": "THRD-001"}
    assert spec["revision"] == 2
    assert (pkg / "addendum/api/api.yaml").exists()
    assert (pkg / "addendum/mock/screens/home.png").exists()
    assert "missing.png" in (pkg / "addendum/LINKS.md").read_text()
    assert (repo / ".cairn/handoff/SPEC-001.zip").exists()
    assert json.loads((pkg / "manifest.json").read_text())["revision"] == 2

    thread = (repo / "threads/THRD-001.md").read_text()
    meta = frontmatter(repo / "threads/THRD-001.md")
    assert meta["status"] == "Handed off"
    assert meta["handoff"]["to"] == "export" and meta["handoff"]["where"] == "platform team"
    assert meta["handoff"]["spec_id"] == "SPEC-001"
    assert meta["outbound_refs"][0] == "spec:SPEC-001"
    assert thread.endswith("Body stays put.\n")
    # The Spec in this repo is untouched; only the package copy gets a source link.
    assert "source" not in frontmatter(repo / "specs/SPEC-001.md")


def test_repo_copies_into_target_checkout(repo, tmp_path_factory):
    install_script(repo)
    target = tmp_path_factory.mktemp("other")
    subprocess.run(["git", "init", "-q", str(target)], check=True)
    r = run(repo, "SPEC-001", "--to", "repo", "--where", str(target))
    assert r.exit_code == 0, r.output
    assert (target / "specs/SPEC-001/spec.md").exists()
    assert (target / "specs/SPEC-001/addendum/api/api.yaml").exists()


def test_in_place_needs_no_where(repo):
    r = run(repo, "SPEC-001", "--to", "in_place")
    assert r.exit_code == 0, r.output
    assert frontmatter(repo / "threads/THRD-001.md")["handoff"] == {
        "to": "in_place", "on": h._dt.date.today().isoformat(), "spec_id": "SPEC-001", "revision": 2}


def test_refuses_thread_not_specified(repo):
    (repo / "threads/THRD-001.md").write_text(THREAD.format(status="Active"))
    r = run(repo, "SPEC-001", "--to", "in_place")
    assert r.exit_code == 1 and "not Specified" in r.output
    assert not (repo / ".cairn/handoff/SPEC-001").exists()


def test_refuses_failed_or_missing_compile(repo):
    report = repo / "specs/SPEC-001.compile_report.md"
    report.write_text("## Verdict: Fail\n")
    assert "says Fail" in run(repo, "SPEC-001", "--to", "in_place").output
    report.unlink()
    assert "is missing" in run(repo, "SPEC-001", "--to", "in_place").output


def test_failed_script_leaves_thread_specified(repo):
    (repo / ".cairn").mkdir(exist_ok=True)
    (repo / h.SCRIPT).write_text("import sys; sys.exit(3)\n")
    r = run(repo, "SPEC-001", "--to", "export", "--where", "team")
    assert r.exit_code == 1 and "code 3" in r.output
    assert frontmatter(repo / "threads/THRD-001.md")["status"] == "Specified"


def test_dry_run_changes_nothing(repo):
    install_script(repo)
    r = run(repo, "SPEC-001", "--to", "export", "--where", "team", "--dry-run")
    assert r.exit_code == 0
    assert (repo / ".cairn/handoff/SPEC-001/spec.md").exists()
    assert not (repo / ".cairn/handoff/SPEC-001.zip").exists()
    assert frontmatter(repo / "threads/THRD-001.md")["status"] == "Specified"


def test_warns_on_non_31_openapi(repo):
    (repo / "design/api.yaml").write_text("openapi: 3.0.3\n")
    r = run(repo, "SPEC-001", "--to", "in_place")
    assert r.exit_code == 0 and "not OpenAPI 3.1 (openapi: 3.0.3)" in r.output


def test_export_needs_where(repo):
    r = run(repo, "SPEC-001", "--to", "export")
    assert r.exit_code == 1 and "needs --where" in r.output


def test_init_installs_script_once(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert runner.invoke(app, ["init", "--here"]).exit_code == 0
    script = tmp_path / h.SCRIPT
    assert "def export" in script.read_text()
    script.write_text("# mine\n")
    runner.invoke(app, ["init", "--here", "--force"])
    assert script.read_text() == "# mine\n"


def overview(repo, system, **meta):
    (repo / "architecture" / system).mkdir(parents=True)
    (repo / "architecture" / system / "overview.md").write_text("---\n" + yaml.safe_dump(meta) + "---\nBody.\n")


def test_unverified_architecture_warns_but_hands_off(repo):
    thread = THREAD.format(status="Specified").replace("owner: pm", "owner: pm\ntouches: [auth, billing, search, payments]")
    (repo / "threads/THRD-001.md").write_text(thread)
    today = h._dt.date.today()
    overview(repo, "auth", readiness="L2", verified=True, last_verified=today, review_ttl="180d")
    overview(repo, "billing", readiness="L1", verified=False)
    overview(repo, "search", readiness="L2", verified=True, last_verified=today - h._dt.timedelta(days=200),
             review_ttl="180d")
    r = run(repo, "SPEC-001", "--to", "in_place")
    assert r.exit_code == 0, r.output
    expected = [h.UNVERIFIED_NOTE.format(level=lvl, system=s)
                for lvl, s in (("L1", "billing"), ("L2, past review_ttl", "search"), ("L0", "payments"))]
    assert frontmatter(repo / ".cairn/handoff/SPEC-001/spec.md")["unverified_architecture"] == expected
    assert json.loads((repo / ".cairn/handoff/SPEC-001/manifest.json").read_text())["unverified_architecture"] == expected
    assert "Warning: Spec relies on unverified L1 Architecture [billing]" in r.output
    assert "[auth]" not in r.output


def test_no_touches_adds_no_warning(repo):
    assert run(repo, "SPEC-001", "--to", "in_place").exit_code == 0
    assert "unverified_architecture" not in frontmatter(repo / ".cairn/handoff/SPEC-001/spec.md")


def test_journey_ref_by_id_is_copied(repo):
    (repo / "journeys").mkdir()
    (repo / "journeys/JRN-001.md").write_text("---\njourney_id: JRN-001\nthread_id: THRD-001\n---\n1. Step.\n")
    thread = repo / "threads/THRD-001.md"
    thread.write_text(thread.read_text().replace("  - spec:SPEC-001\n", "  - spec:SPEC-001\n  - journey:JRN-001\n"))
    res = run(repo, "SPEC-001", "--to", "in_place", "--dry-run")
    assert res.exit_code == 0, res.output
    assert (repo / ".cairn/handoff/SPEC-001/addendum/journey/JRN-001.md").exists()
