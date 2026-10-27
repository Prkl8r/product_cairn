import json

from typer.testing import CliRunner

from cairn_cli import jury
from cairn_cli.cli import app


def test_coin_gives_debaters_different_models_and_judge_opus():
    seen = set()
    for seed in range(40):
        r = jury.draw({}, seed)
        assert r["judge"] == "opus" and r["draw"] == "coin"
        assert {r["advocate"], r["skeptic"]} == {"opus", "sonnet"}
        seen.add(r["advocate"])
    assert seen == {"opus", "sonnet"}  # both outcomes actually happen


def test_seed_repeats_draw():
    assert jury.draw({}, 7) == jury.draw({}, 7)


def test_fixed_and_pinned():
    assert jury.draw({"draw": "fixed"})["advocate"] == "opus"
    r = jury.draw({"models": {"skeptic": "opus"}}, 1)
    assert (r["advocate"], r["skeptic"], r["draw"]) == ("sonnet", "opus", "config")


def test_same_model_warns():
    r = jury.draw({"models": {"advocate": "sonnet", "skeptic": "sonnet"}})
    assert r["warnings"]


def test_cli_prints_json(tmp_path):
    res = CliRunner().invoke(app, ["jury-draw", "--seed", "3", "--path", str(tmp_path)])
    assert res.exit_code == 0, res.output
    assert json.loads(res.output)["seed"] == 3
