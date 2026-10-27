import json

import pytest
from typer.testing import CliRunner

from cairn_cli.cli import app

runner = CliRunner()

SIGNAL = "---\nsignal_id: IDEA-001\ntype: idea\nsource: dev\ncaptured_on: 2026-10-01\ndata_class: internal\n---\nRain alerts per hour.\n"
SECRET = "---\nsignal_id: FDBK-001\ntype: feedback\nsource: support\ncaptured_on: 2026-10-01\ndata_class: restricted\n---\nA named user.\n"
THREAD = ("---\nthread_id: THRD-001\nstage: Framing\nstatus: Active\ninbound_refs: [\"idea:IDEA-001\"]\n"
          "outbound_refs: []\n---\nHourly rain alerts.\n")


@pytest.fixture
def repo(tmp_path):
    root = tmp_path / "product"
    result = runner.invoke(app, ["init", str(root), "--agent", "claude"])
    assert result.exit_code == 0, result.output
    (root / "signals/idea/IDEA-001.md").parent.mkdir(parents=True, exist_ok=True)
    (root / "signals/idea/IDEA-001.md").write_text(SIGNAL)
    (root / "signals/feedback").mkdir(parents=True, exist_ok=True)
    (root / "signals/feedback/FDBK-001.md").write_text(SECRET)
    (root / "threads/THRD-001.md").write_text(THREAD)
    return root


def test_init_is_idempotent_and_keeps_charter(repo):
    (repo / "charter.yaml").write_text("product: mine\n")
    result = runner.invoke(app, ["init", str(repo), "--agent", "claude"])
    assert result.exit_code == 0, result.output
    assert (repo / "charter.yaml").read_text() == "product: mine\n"
    assert (repo / ".cairn/package.lock").exists()
    assert (repo / ".claude/skills/check-spec/SKILL.md").exists()


def test_doctor_healthy_then_missing_skill(repo):
    result = runner.invoke(app, ["doctor", str(repo)])
    assert result.exit_code == 0, result.output
    assert "healthy" in result.output
    (repo / ".claude/skills/check-spec/SKILL.md").unlink()
    result = runner.invoke(app, ["doctor", str(repo)])
    assert result.exit_code == 1
    assert "MISSING .claude/skills/check-spec/SKILL.md" in result.output


def test_doctor_without_init_fails(tmp_path):
    result = runner.invoke(app, ["doctor", str(tmp_path)])
    assert result.exit_code == 1
    assert "has not run `cairn init`" in result.output


def test_doctor_warns_on_unknown_keys_unless_listed(repo):
    (repo / "threads/THRD-001.md").write_text(THREAD.replace("status: Active", "status: Active\nfast_track: true"))
    result = runner.invoke(app, ["doctor", str(repo)])
    assert "THRD-001 has unknown key `fast_track` (did you mean `track`?)" in result.output
    config = repo / ".cairn/config.yaml"
    config.write_text(config.read_text().replace("extra_keys: []", "extra_keys: [fast_track]"))
    assert "unknown key" not in runner.invoke(app, ["doctor", str(repo)]).output


def test_doctor_warns_on_broken_refs(repo):
    (repo / "threads/THRD-001.md").write_text(THREAD.replace("idea:IDEA-001", "idea:IDEA-999"))
    assert "THRD-001 references missing files" in runner.invoke(app, ["doctor", str(repo)]).output


def test_ledger_lists_signals_and_threads(repo):
    result = runner.invoke(app, ["ledger", "--path", str(repo)])
    assert result.exit_code == 0, result.output
    assert "Asked — 2 signals" in result.output
    assert "THRD-001" in result.output and "[restricted]" in result.output
    assert "nothing yet" in result.output


def test_ledger_json_hides_restricted(repo):
    snap = json.loads(runner.invoke(app, ["ledger", "--path", str(repo), "--json"]).output)
    assert "FDBK-001" not in json.dumps(snap)
    snap = json.loads(runner.invoke(app, ["ledger", "--path", str(repo), "--json", "--include-restricted"]).output)
    assert "FDBK-001" in json.dumps(snap)


def test_find_by_words_and_by_id(repo):
    result = runner.invoke(app, ["find", "rain", "--path", str(repo)])
    assert result.exit_code == 0 and "IDEA-001" in result.output
    lineage = json.loads(runner.invoke(app, ["find", "THRD-001", "--path", str(repo), "--json"]).output)
    assert lineage["lineage"] and {"THRD-001", "IDEA-001"} <= {r["id"] for r in lineage["results"]}
    assert runner.invoke(app, ["find", "zzzz", "--path", str(repo)]).exit_code == 1


def test_snapshot_writes_status_files(repo):
    result = runner.invoke(app, ["snapshot", "--path", str(repo)])
    assert result.exit_code == 0, result.output
    snap = json.loads((repo / "STATUS.json").read_text())
    assert [t["id"] for t in snap["threads"]] == ["THRD-001"]
    assert "FDBK-001" not in (repo / "STATUS.md").read_text()


def test_ledger_json_lists_untriaged_signals(repo):
    snap = json.loads(runner.invoke(app, ["ledger", "--path", str(repo), "--json", "--include-restricted"]).output)
    assert snap["untriaged"] == ["FDBK-001"]
