"""Jury seat models: which model each of the Advocate, Skeptic and Judge runs on.

The Judge is fixed (default opus). The two debaters get the two `debate_models` in a random order
unless `draw: fixed` or a seat is pinned under `models`, so the stronger model doesn't always argue
for the proposal. Seats pinned in config always win.
"""
from __future__ import annotations

import random
from pathlib import Path

import yaml

DEBATE_MODELS = ["opus", "sonnet"]
JUDGE_MODEL = "opus"
FIXED = {"advocate": "opus", "skeptic": "sonnet"}


def settings(config_path: Path) -> dict:
    if not config_path.exists():
        return {}
    return (yaml.safe_load(config_path.read_text()) or {}).get("jury") or {}


def draw(jury: dict, seed: int | None = None) -> dict:
    """Returns {advocate, skeptic, judge, draw, seed, warnings}."""
    pinned = {k: v for k, v in (jury.get("models") or {}).items() if v}
    pair = [m for m in (jury.get("debate_models") or DEBATE_MODELS) if m][:2]
    mode = str(jury.get("draw") or "coin")
    if seed is None:
        seed = random.SystemRandom().randrange(1_000_000)
    seats = {"judge": pinned.get("judge", JUDGE_MODEL)}
    warnings: list[str] = []

    if mode == "fixed" or len(pair) < 2:
        seats["advocate"] = pinned.get("advocate", FIXED["advocate"])
        seats["skeptic"] = pinned.get("skeptic", FIXED["skeptic"])
        how = "fixed"
    elif "advocate" in pinned and "skeptic" in pinned:
        seats["advocate"], seats["skeptic"] = pinned["advocate"], pinned["skeptic"]
        how = "config"
    elif "advocate" in pinned or "skeptic" in pinned:
        # One debater pinned: the other takes the model from the pair that differs from it.
        seat, other = ("advocate", "skeptic") if "advocate" in pinned else ("skeptic", "advocate")
        seats[seat] = pinned[seat]
        seats[other] = next((m for m in pair if m != pinned[seat]), pair[0])
        how = "config"
    else:
        order = pair[:]
        random.Random(seed).shuffle(order)
        seats["advocate"], seats["skeptic"] = order
        how = "coin"

    if seats["advocate"] == seats["skeptic"]:
        warnings.append(f"Advocate and Skeptic both run on {seats['advocate']}, so the critique isn't independent.")
    return {**seats, "draw": how, "seed": seed if how == "coin" else None, "warnings": warnings}
