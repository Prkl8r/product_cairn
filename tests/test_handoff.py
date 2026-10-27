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
scope_decision: single
verdict_ref: threads/THRD-001-verdict.md
jury_seats: [{{seat: advocate, model: sonnet, calls: 3}}, {{seat: skeptic, model: opus, calls: 3}}, {{seat: judge, model: opus, calls: 1}}]
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
sections:
  problem: "A problem."
  out_of_scope: ["Nothing else."]
  error_states: ["An error."]
  empty_states: ["An empty state."]
  enablement_deps: "n/a: solo"
slices:
  - {id: S1, name: Core, order: 1, verify: "It works."}
criteria:
  - id: AC-001
    slice: S1
    type: binary
    text: "The idea is shown."
    trace:
      - {ref: "idea:IDEA-001", basis: direct, quote: "An idea."}
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
    (tmp_path / "threads/THRD-001-verdict.md").write_text("verdict: proceed\n")
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
    assert meta["handoffs"][0]["to"] == "export" and meta["handoffs"][0]["where"] == "platform team"
    assert meta["handoffs"][0]["spec_id"] == "SPEC-001"
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
    assert frontmatter(repo / "threads/THRD-001.md")["handoffs"][0] == {
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


def multi_spec(repo, spec_status="specified"):
    """THRD-001 with SPEC-001 drafted and one planned Spec not drafted yet."""
    thread = repo / "threads/THRD-001.md"
    thread.write_text(THREAD.format(status="Active").replace(
        "---\n\nBody", "planned_specs:\n  - key: core\n    spec_id: SPEC-001\n  - key: refine\n    spec_id: null\n---\n\nBody"))
    spec = repo / "specs/SPEC-001.md"
    spec.write_text(SPEC.replace("revision: 2\n", f"revision: 2\nspec_status: {spec_status}\n"))
    return thread, spec


def test_one_spec_of_several_hands_off_and_thread_stays_active(repo):
    thread, spec = multi_spec(repo)
    r = run(repo, "SPEC-001", "--to", "in_place")
    assert r.exit_code == 0, r.output
    assert "stays Active" in r.output and "(not drafted)" in r.output
    meta = frontmatter(thread)
    assert meta["status"] == "Active" and "handoff" not in meta
    assert [h["spec_id"] for h in meta["handoffs"]] == ["SPEC-001"]
    assert frontmatter(spec)["spec_status"] == "handed_off"


def test_last_spec_hands_off_the_thread(repo):
    thread, _ = multi_spec(repo)
    (repo / "specs/SPEC-002.md").write_text(SPEC.replace("spec_id: SPEC-001", "spec_id: SPEC-002\nspec_status: specified"))
    (repo / "specs/SPEC-002.compile_report.md").write_text("## Verdict: Pass\n")
    thread.write_text(thread.read_text().replace("    spec_id: null", "    spec_id: SPEC-002")
                      .replace("  - spec:SPEC-001\n", "  - spec:SPEC-001\n  - spec:SPEC-002\n"))
    assert run(repo, "SPEC-001", "--to", "in_place").exit_code == 0
    assert frontmatter(thread)["status"] == "Active"
    assert run(repo, "SPEC-002", "--to", "in_place").exit_code == 0
    meta = frontmatter(thread)
    assert meta["status"] == "Handed off" and len(meta["handoffs"]) == 2


def test_refuses_spec_not_specified(repo):
    multi_spec(repo, spec_status="drafted")
    r = run(repo, "SPEC-001", "--to", "in_place")
    assert r.exit_code == 1 and "not specified" in r.output


def test_old_single_handoff_record_is_kept(repo):
    thread, _ = multi_spec(repo)
    thread.write_text(thread.read_text().replace("planned_specs:", "handoff:\n  to: export\n  spec_id: SPEC-000\n  revision: 1\nplanned_specs:"))
    assert run(repo, "SPEC-001", "--to", "in_place").exit_code == 0
    assert [h["spec_id"] for h in frontmatter(thread)["handoffs"]] == ["SPEC-000", "SPEC-001"]


def write_targets(repo, targets, default=None):
    (repo / ".cairn").mkdir(exist_ok=True)
    (repo / h.CONFIG).write_text(yaml.safe_dump({"handoff": {"default": default, "targets": targets}}))


def test_script_target_runs_command_with_placeholders(repo):
    write_targets(repo, {"zip": {"kind": "script", "run": "echo {spec_id} {thread_id} > out.txt && test -f {spec}"}})
    r = run(repo, "SPEC-001", "--target", "zip")
    assert r.exit_code == 0, r.output
    assert (repo / "out.txt").read_text().strip() == "SPEC-001 THRD-001"
    rec = frontmatter(repo / "threads/THRD-001.md")["handoffs"][0]
    assert rec["to"] == "zip" and rec["kind"] == "script"


def test_failed_target_script_leaves_thread_specified(repo):
    write_targets(repo, {"bad": {"kind": "script", "run": "exit 4"}})
    r = run(repo, "SPEC-001", "--target", "bad")
    assert r.exit_code == 1 and "code 4" in r.output
    assert frontmatter(repo / "threads/THRD-001.md")["status"] == "Specified"


def test_agent_kind_needs_dry_run_or_delivered(repo):
    write_targets(repo, {"speckit": {"kind": "speckit"}}, default="speckit")
    r = run(repo, "SPEC-001", "--target", "speckit")
    assert r.exit_code == 1 and "--delivered" in r.output
    assert frontmatter(repo / "threads/THRD-001.md")["status"] == "Specified"

    r = run(repo, "SPEC-001", "--target", "default", "--dry-run")
    assert r.exit_code == 0 and "Target: speckit (skill)" in r.output
    assert frontmatter(repo / "threads/THRD-001.md")["status"] == "Specified"

    r = run(repo, "SPEC-001", "--target", "speckit", "--delivered")
    assert r.exit_code == 0, r.output
    meta = frontmatter(repo / "threads/THRD-001.md")
    assert meta["status"] == "Handed off"
    assert meta["handoffs"][0]["to"] == "speckit" and meta["handoffs"][0]["kind"] == "skill"


def test_target_errors(repo):
    assert "exactly one" in run(repo, "SPEC-001").output
    assert "exactly one" in run(repo, "SPEC-001", "--to", "in_place", "--target", "x").output
    assert "goes with --target" in run(repo, "SPEC-001", "--to", "in_place", "--delivered").output
    assert "no --target given" in run(repo, "SPEC-001", "--target", "default", "--dry-run").output
    write_targets(repo, {"s": {"kind": "skill"}, "w": {"kind": "weird"}})
    assert "known: s, w" in run(repo, "SPEC-001", "--target", "nope", "--dry-run").output
    assert "needs: skill" in run(repo, "SPEC-001", "--target", "s", "--dry-run").output
    assert "kind 'weird'" in run(repo, "SPEC-001", "--target", "w", "--dry-run").output


def test_handoff_targets_lists_config(repo):
    write_targets(repo, {"speckit": {"kind": "speckit"}}, default="speckit")
    r = runner.invoke(app, ["handoff-targets", "--path", str(repo)])
    t = json.loads(r.output)["targets"]["speckit"]
    assert t["integration"] == "speckit" and t["kind"] == "skill" and t["skill"] == "speckit-specify"


def test_fill_keeps_unknown_braces():
    assert h.fill("a {spec_id} ${HOME} {x}", {"spec_id": "S"}) == "a S ${HOME} {x}"


def test_set_keys_replaces_in_place_and_keeps_comment():
    text = "---\nid: T\nstatus: Specified  # waits on SPEC-002\nhandoffs:\n- a: 1\ntitle: x\n---\nbody"
    out = h.set_keys(text, {"status": "Specified", "handoffs": [{"a": 1}, {"b": 2}], "new": 1})
    assert out == ("---\nid: T\nstatus: Specified  # waits on SPEC-002\nhandoffs:\n- a: 1\n- b: 2\n"
                   "title: x\nnew: 1\n---\nbody")


def test_integration_target_merges_and_overrides(repo):
    write_targets(repo, {"sk": {"integration": "speckit", "skill": "my-specify"}}, default="sk")
    r = run(repo, "SPEC-001", "--target", "sk", "--dry-run")
    assert r.exit_code == 0 and "Target: sk (skill)" in r.output
    assert "expects .specify" in r.output  # not set up in the test repo
    t = json.loads(CliRunner().invoke(app, ["handoff-targets", "--path", str(repo)]).output)["targets"]["sk"]
    assert t["skill"] == "my-specify" and "{spec}" in t["args"]


def test_template_integration_needs_template_and_out(repo):
    write_targets(repo, {"t": {"integration": "template"}})
    assert "needs: template, out" in run(repo, "SPEC-001", "--target", "t", "--dry-run").output
    write_targets(repo, {"t": {"integration": "template", "template": "tpl.md", "out": "docs/{spec_id}.md"}})
    assert "doesn't exist" in run(repo, "SPEC-001", "--target", "t", "--dry-run").output
    (repo / "tpl.md").write_text("# {{title}}\n")
    r = run(repo, "SPEC-001", "--target", "t", "--dry-run")
    assert r.exit_code == 0 and "Target: t (template)" in r.output


def test_project_integration_overrides_builtin_and_unknown_fails(repo):
    (repo / ".cairn/integrations").mkdir(parents=True)
    (repo / ".cairn/integrations/openspec.yaml").write_text("kind: script\nrun: \"true\"\n")
    write_targets(repo, {"o": {"integration": "openspec"}, "x": {"integration": "nope"}})
    assert run(repo, "SPEC-001", "--target", "o").exit_code == 0
    assert "isn't built in" in run(repo, "SPEC-001", "--target", "x", "--dry-run").output


def test_script_integration_fills_target_fields(repo):
    (repo / ".cairn/integrations").mkdir(parents=True)
    (repo / ".cairn/integrations/push.yaml").write_text(
        "kind: script\nneeds: [repo]\nrun: \"echo {spec_id} {repo} {template} > sent.txt\"\n")
    write_targets(repo, {"p": {"integration": "push"}})
    assert "needs: repo" in run(repo, "SPEC-001", "--target", "p").output
    write_targets(repo, {"p": {"integration": "push", "repo": "../other", "template": "t.md"}})
    assert run(repo, "SPEC-001", "--target", "p").exit_code == 0
    assert (repo / "sent.txt").read_text().split() == ["SPEC-001", "../other", "t.md"]
