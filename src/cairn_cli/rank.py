"""Optional Thread priority and size, scored by a scheme the user picks in .cairn/config.yaml.

A sorting aid for busy weeks, not a backlog tool: both fields are optional, and a Thread without
them simply sorts last. Level schemes are ordered lists (first = highest priority, or smallest size).
Score schemes (RICE, ICE, or your own) take named fields and a formula; a higher score sorts first.
"""
from __future__ import annotations

import ast
import operator
from pathlib import Path

import yaml

PRIORITY_SCHEMES = {
    "hml": {"levels": ["High", "Medium", "Low"]},
    "p-levels": {"levels": ["P0", "P1", "P2", "P3"]},
    "moscow": {"levels": ["Must", "Should", "Could", "Won't"]},
    "rice": {"fields": ["reach", "impact", "confidence", "effort"],
             "formula": "reach * impact * confidence / effort"},
    "ice": {"fields": ["impact", "confidence", "ease"], "formula": "impact * confidence * ease"},
}
SIZE_SCHEMES = {
    "sml": {"levels": ["Small", "Medium", "Large"]},
    "tshirt": {"levels": ["XS", "S", "M", "L", "XL"]},
    "points": {"levels": [1, 2, 3, 5, 8, 13]},
    "days": {"levels": "number"},  # any positive number of ideal days
}
DEFAULTS = {"priority": "hml", "size": "sml"}

_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}


def _config(root: Path) -> dict:
    cfg = root / ".cairn" / "config.yaml"
    try:
        return (yaml.safe_load(cfg.read_text(encoding="utf-8")) or {}) if cfg.exists() else {}
    except yaml.YAMLError:
        return {}


def scheme(root: Path, field: str, config: dict | None = None) -> dict:
    """The scheme for `priority` or `size`: a built-in name, or a custom {levels} / {fields, formula}."""
    built_in = PRIORITY_SCHEMES if field == "priority" else SIZE_SCHEMES
    raw = ((config if config is not None else _config(root)).get(field) or {}).get("scheme", DEFAULTS[field])
    if isinstance(raw, str):
        return dict(built_in.get(raw.lower()) or built_in[DEFAULTS[field]], name=raw.lower())
    return dict(raw, name="custom") if isinstance(raw, dict) else dict(built_in[DEFAULTS[field]], name=DEFAULTS[field])


def _eval(formula: str, values: dict[str, float]) -> float:
    """Arithmetic only (+ - * / and parentheses) over the named fields. No calls, no attributes."""
    def walk(node):
        if isinstance(node, ast.Expression):
            return walk(node.body)
        if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](walk(node.left), walk(node.right))
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.Name) and node.id in values:
            return values[node.id]
        raise ValueError(f"can't use `{ast.unparse(node)}` in a formula")
    return float(walk(ast.parse(formula, mode="eval")))


def size_number(value, size_scheme: dict) -> float | None:
    """A size as a number: its position in a level scheme (1 = smallest), or the number itself."""
    levels = size_scheme.get("levels")
    if levels == "number":
        return float(value) if isinstance(value, (int, float)) and value > 0 else None
    norm = [str(l).lower() for l in levels or []]
    if str(value).lower() in norm:
        hit = levels[norm.index(str(value).lower())]
        return float(hit) if isinstance(hit, (int, float)) else float(norm.index(str(value).lower()) + 1)
    return None


def priority_score(meta: dict, prio: dict, size_scheme: dict | None = None) -> tuple[float | None, str | None]:
    """(score, problem). Higher scores sort first; level schemes score by position. None when unset."""
    value = meta.get("priority")
    if value is None:
        return None, None
    if "levels" in prio:
        norm = [str(l).lower() for l in prio["levels"]]
        if str(value).lower() not in norm:
            return None, f"priority `{value}` isn't one of {', '.join(map(str, prio['levels']))}"
        return float(len(norm) - norm.index(str(value).lower())), None
    if not isinstance(value, dict):
        return None, f"priority should list {', '.join(prio['fields'])} for the {prio['name']} scheme"
    values = dict(value)
    # RICE-style effort can default from size, so the PM isn't asked twice.
    if "effort" in prio["fields"] and values.get("effort") is None and size_scheme and meta.get("size") is not None:
        values["effort"] = size_number(meta["size"], size_scheme)
    missing = [f for f in prio["fields"] if not isinstance(values.get(f), (int, float))]
    if missing:
        return None, f"priority is missing {', '.join(missing)}"
    try:
        return _eval(prio["formula"], {f: float(values[f]) for f in prio["fields"]}), None
    except (ValueError, ZeroDivisionError, SyntaxError) as e:
        return None, f"priority formula: {e}"


def size_problem(meta: dict, size_scheme: dict) -> str | None:
    value = meta.get("size")
    if value is None or size_number(value, size_scheme) is not None:
        return None
    levels = size_scheme.get("levels")
    allowed = "a positive number of days" if levels == "number" else ", ".join(map(str, levels or []))
    return f"size `{value}` isn't {allowed}"


def annotate(root: Path, threads: list[dict], metas: dict[str, dict]) -> list[dict]:
    """Add `priority_score` to each Thread dict and return them sorted: highest priority first, unset last."""
    config = _config(root)
    prio, size = scheme(root, "priority", config), scheme(root, "size", config)
    for t in threads:
        score, _ = priority_score(metas[t["id"]], prio, size)
        if score is not None:
            t["priority_score"] = round(score, 3)
    return sorted(threads, key=lambda t: (t.get("priority_score") is None, -(t.get("priority_score") or 0)))


def problems(root: Path, meta: dict) -> list[str]:
    """What `doctor` warns about: values that don't fit the configured schemes."""
    config = _config(root)
    prio, size = scheme(root, "priority", config), scheme(root, "size", config)
    out = [p for p in (priority_score(meta, prio, size)[1], size_problem(meta, size)) if p]
    for part in meta.get("planned_specs") or []:
        if isinstance(part, dict) and (p := size_problem(part, size)):
            out.append(f"planned Spec `{part.get('key', '?')}`: {p}")
    return out


def label(meta: dict) -> str:
    """Short display of priority and size, e.g. 'High · M' or 'RICE · L'."""
    p = meta.get("priority")
    p = "scored" if isinstance(p, dict) else p
    return " · ".join(str(x) for x in (p, meta.get("size")) if x is not None) or "-"
