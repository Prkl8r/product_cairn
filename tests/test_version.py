import json
import tomllib
from pathlib import Path

from cairn_cli import __version__

ROOT = Path(__file__).resolve().parents[1]


def test_versions_match():
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
    plugin = json.loads((ROOT / "src/cairn_cli/templates/.claude-plugin/plugin.json").read_text())["version"]
    assert __version__ == pyproject == plugin
