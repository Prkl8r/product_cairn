import pytest
import yaml
from typer.testing import CliRunner

from cairn_cli import compile as c
from cairn_cli import ledger
from cairn_cli.cli import app

runner = CliRunner()

THREAD = """---
thread_id: THRD-001
stage: Validating
status: Active
owner: pm
inbound_refs: ["idea:IDEA-001"]
outbound_refs: ["spec:SPEC-001"]
---

A-01: users want it.
"""


def spec_meta(**over):
    meta = {
        "spec_id": "SPEC-001", "thread_id": "THRD-001", "track": "normal",
        "sections": {"problem": "p", "out_of_scope": ["x"], "error_states": ["e"], "empty_states": ["m"],
                     "enablement_deps": "n/a: solo"},
        "slices": [{"id": "S1", "name": "Core", "order": 1, "verify": "works"}],
        "criteria": [{"id": "AC-001", "slice": "S1", "type": "binary", "modality": "mobile", "text": "Shows it.",
                      "trace": [{"ref": "idea:IDEA-001", "basis": "direct", "quote": "an IDEA"}]}],
    }
    meta.update(over)
    return meta


@pytest.fixture
def repo(tmp_path):
    for d in ("signals/idea", "threads", "specs", "architecture/api"):
        (tmp_path / d).mkdir(parents=True)
    (tmp_path / "signals/idea/IDEA-001.md").write_text("---\nsignal_id: IDEA-001\ntype: idea\n---\nAn idea.\n")
    (tmp_path / "architecture/api/overview.md").write_text("---\nowner: pm\n---\nServes /status.\n")
    (tmp_path / "threads/THRD-001.md").write_text(THREAD)
    (tmp_path / "charter.yaml").write_text("ui_presence: true\n")
    return tmp_path


def write(repo, meta):
    (repo / "specs/SPEC-001.md").write_text("---\n" + yaml.safe_dump(meta, sort_keys=False) + "---\nBody.\n")


def rules(repo, meta):
    write(repo, meta)
    return {(f.rule, f.where) for f in c.errors(c.check(repo, "SPEC-001"))}


def test_clean_spec_passes(repo):
    assert rules(repo, spec_meta()) == set()


def test_missing_keys_and_sections(repo):
    meta = spec_meta()
    del meta["slices"]
    meta["sections"]["error_states"] = []
    found = rules(repo, meta)
    assert ("C01", "slices") in found
    assert ("C10", "error_states") in found


def test_thread_must_list_spec_and_be_at_validating(repo):
    (repo / "threads/THRD-001.md").write_text(THREAD.replace("stage: Validating", "stage: Framing")
                                              .replace('["spec:SPEC-001"]', "[]"))
    found = {r for r, _ in rules(repo, spec_meta())}
    assert found == {"C02"}
    assert rules(repo, spec_meta(track="fast")) == {("C02", "THRD-001")}  # only the missing outbound ref


def test_refs_resolve_by_id_path_or_repo_file(repo):
    traces = [{"ref": "architecture/api/overview.md", "basis": "direct", "quote": "serves /status"},
              {"ref": "api/overview.md", "basis": "interpreted"},
              {"ref": "charter.yaml", "basis": "decided", "decided_by": "pm"},
              {"ref": "lib:missing", "basis": "interpreted"},
              {"ref": "signals/idea/raw/IDEA-001.md", "basis": "interpreted"}]
    meta = spec_meta()
    meta["criteria"][0]["trace"] = traces
    found = rules(repo, meta)
    assert sorted(found) == [("C05", "AC-001")]
    assert len([f for f in c.check(repo, "SPEC-001") if f.rule == "C05"]) == 2  # missing + raw


def test_paraphrased_quote_fails(repo):
    meta = spec_meta()
    meta["criteria"][0]["trace"][0]["quote"] = "A great idea."
    assert rules(repo, meta) == {("C06", "AC-001")}


def test_modality_vague_terms_and_threshold(repo):
    (repo / "charter.yaml").write_text("ui_presence: false\n")
    meta = spec_meta()
    meta["criteria"][0]["text"] = "Loads fast."
    meta["criteria"].append({"id": "AC-002", "slice": "S1", "type": "threshold", "modality": "api",
                             "text": "Refreshes every 30 minutes.", "threshold": {"metric": "refresh"},
                             "trace": [{"ref": "idea:IDEA-001", "basis": "interpreted"}]})
    found = rules(repo, meta)
    assert {("C07", "AC-001"), ("C08", "AC-001"), ("C09", "AC-002")} <= found


def test_open_questions_and_slices(repo):
    meta = spec_meta(open_questions=[{"text": "q", "status": "deferred", "reason": "later"},
                                     {"text": "q2", "status": "pending"}])
    meta["slices"].append({"id": "S2", "name": "Empty"})
    meta["criteria"][0]["slice"] = "S9"
    found = rules(repo, meta)
    assert {("C20", "open_questions[1]"), ("C20", "open_questions[2]"),
            ("C21", "AC-001"), ("C21", "S1"), ("C21", "S2")} <= found


def test_basis_fields_and_assumptions(repo):
    meta = spec_meta()
    meta["criteria"][0]["trace"] = [{"ref": "idea:IDEA-001", "basis": "direct"},
                                    {"ref": "idea:IDEA-001", "basis": "inferred", "assumption": "A-09"},
                                    {"ref": "idea:IDEA-001", "basis": "guessed"}]
    write(repo, meta)
    assert [f.message.split(" ")[0] for f in c.check(repo, "SPEC-001") if f.rule == "C23"] == \
        ["`direct`", "assumption", "trace"]
    meta["criteria"][0]["trace"] = [{"ref": "idea:IDEA-001", "basis": "inferred", "assumption": "A-01"}]
    write(repo, meta)
    assert [(f.rule, f.severity) for f in c.check(repo, "SPEC-001")] == [("C23", "Warn")]  # all inferred


def test_cli_exit_code_and_markdown(repo):
    write(repo, spec_meta())
    r = runner.invoke(app, ["check", "SPEC-001", "--markdown", "--path", str(repo)])
    assert r.exit_code == 0 and "| C05 | Pass |" in r.output
    meta = spec_meta()
    meta["criteria"][0]["trace"][0]["ref"] = "idea:NOPE"
    write(repo, meta)
    r = runner.invoke(app, ["check", "SPEC-001", "--path", str(repo)])
    assert r.exit_code == 1 and "C05" in r.output


def test_handoff_refuses_despite_pass_report(repo):
    meta = spec_meta()
    meta["criteria"][0]["trace"][0]["ref"] = "idea:NOPE"
    write(repo, meta)
    (repo / "threads/THRD-001.md").write_text(THREAD.replace("status: Active", "status: Specified"))
    (repo / "specs/SPEC-001.compile_report.md").write_text("## Verdict: Pass\n")
    r = runner.invoke(app, ["handoff", "SPEC-001", "--to", "in_place", "--dry-run", "--path", str(repo)])
    assert r.exit_code == 1
    assert "whatever its compile report says" in r.output and "idea:NOPE" in r.output


def test_ledger_links_path_form_refs(repo):
    meta = spec_meta()
    meta["criteria"][0]["trace"].append({"ref": "architecture/api/overview.md", "basis": "interpreted"})
    write(repo, meta)
    docs = ledger.load(repo)
    assert docs["SPEC-001"].broken == []
    assert "api/overview" in docs["SPEC-001"].links


@pytest.mark.parametrize("text", ["Shows the banner within or in place of the card.",
                                  "Either shows a toast or logs the error.", "Retries and/or alerts."])
def test_either_or_wording_fails(repo, text):
    meta = spec_meta()
    meta["criteria"][0]["text"] = text
    assert rules(repo, meta) == {("C08", "AC-001")}


def test_plain_or_passes(repo):
    meta = spec_meta()
    meta["criteria"][0]["text"] = "Shows rain or snow icons."
    assert rules(repo, meta) == set()
