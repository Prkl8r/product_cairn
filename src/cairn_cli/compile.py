"""The mechanical half of check-spec: the rules that need no judgment, run as code.

`cairn check` prints these, the check-spec skill copies them into the compile report instead of
re-deriving them, and `cairn handoff` refuses a Spec with any Error here, whatever the report says.
Rules that need reading for meaning (C11-C14, C16-C19, C22, C24-C26) stay with the skill.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from . import ledger as _ledger

MECHANICAL = ["C01", "C02", "C04", "C05", "C06", "C07", "C08", "C09", "C10", "C20", "C21", "C23", "C27", "C28"]
REQUIRED_KEYS = {"spec_id": str, "thread_id": str, "sections": dict, "slices": list, "criteria": list}
SECTIONS = ["problem", "out_of_scope", "error_states", "empty_states", "enablement_deps"]
VAGUE = ["fast", "intuitive", "user-friendly", "appropriate", "robust", "should"]  # check-spec C08
BASES = {"direct": "quote", "interpreted": None, "inferred": "assumption", "decided": "decided_by"}
EITHER_OR = [r"\beither\b.+\bor\b", r"\b(\w+) or in place of\b", r"\band/or\b"]  # C08: two outcomes, can't fail
SCOPE_DECISIONS = ["single", "multi_spec", "split"]  # `deferred` must be resolved before drafting
QUESTION_STATUSES = {"answered", "deferred", "out_of_scope"}


@dataclass
class Finding:
    rule: str
    severity: str  # Error | Warn
    where: str     # criterion, slice, or field id
    message: str


def _norm(text: str) -> str:
    return " ".join(re.sub(r"[\"'`*_]", "", text).lower().split())


def _criteria(spec: _ledger.Doc) -> list[dict]:
    return [c for c in spec.meta.get("criteria") or [] if isinstance(c, dict)]


def check(root: Path, spec_id: str, docs: dict[str, _ledger.Doc] | None = None) -> list[Finding]:
    docs = docs if docs is not None else _ledger.load(root)
    spec = docs.get(spec_id)
    if not spec or spec.kind != "spec":
        return [Finding("C01", "Error", spec_id, f"no Spec with id {spec_id} under specs/")]
    out: list[Finding] = []
    err = lambda r, w, m: out.append(Finding(r, "Error", w, m))
    warn = lambda r, w, m: out.append(Finding(r, "Warn", w, m))
    meta = spec.meta

    # C01: required keys, correctly typed.
    for key, typ in REQUIRED_KEYS.items():
        if key not in meta or meta[key] is None:
            err("C01", key, f"missing required key `{key}`")
        elif not isinstance(meta[key], typ):
            err("C01", key, f"`{key}` should be a {typ.__name__}")
    ids = [c.get("id") for c in _criteria(spec)]
    for dup in sorted({i for i in ids if i and ids.count(i) > 1}):
        err("C01", dup, "criterion id used more than once")
    if any(not i for i in ids):
        err("C01", "criteria", "a criterion has no `id`")

    # C02: parent Thread exists, lists this Spec, and is at the right stage for the track.
    thread = docs.get(str(meta.get("thread_id", "")))
    if not thread or thread.kind != "thread":
        err("C02", "thread_id", f"parent Thread {meta.get('thread_id')} not found under threads/")
    else:
        if spec_id not in {_ledger.ref_id(r) for r in thread.meta.get("outbound_refs") or []}:
            err("C02", thread.id, f"{thread.id} doesn't list {spec_id} in outbound_refs")
        stage, status = _ledger.stage_status(thread.meta)
        if meta.get("track", "normal") != "fast" and stage != "Validating":
            err("C02", thread.id, f"normal track needs {thread.id} at Validating, it's at {stage}")
        if status in ("Parked", "Rejected"):
            err("C02", thread.id, f"{thread.id} is {status}")
        # C27: the scope check ran and the PM's answer is on the Thread.
        scope = thread.meta.get("scope_decision")
        if scope not in SCOPE_DECISIONS:
            err("C27", thread.id, f"{thread.id} has no scope_decision; run the scope check "
                                  f"({', '.join(SCOPE_DECISIONS)})" if scope is None else
                                  f"scope_decision `{scope}`; resolve it to one of {', '.join(SCOPE_DECISIONS)}")
        elif scope == "single" and len(meta.get("slices") or []) >= 4:
            warn("C27", thread.id, f"scope_decision is single but {spec_id} has "
                                   f"{len(meta['slices'])} slices; worth asking whether it's several Specs")
        # C28: on the normal track, the jury's Judge seat ran and its verdict is on file.
        if meta.get("track", "normal") != "fast":
            seats = {x.get("seat") for x in thread.meta.get("jury_seats") or [] if isinstance(x, dict)}
            if "judge" not in seats:
                err("C28", thread.id, f"{thread.id} has no `judge` in jury_seats; rerun jury-duty, don't write the verdict by hand")
            missing = [x for x in ("advocate", "skeptic") if x not in seats]
            if missing and "judge" in seats:
                warn("C28", thread.id, f"jury_seats has no {', '.join(missing)}")
            ref = str(thread.meta.get("verdict_ref") or "")
            if not ref or not (root / ref).is_file():
                err("C28", thread.id, f"verdict_ref `{ref}` isn't a file in this repo" if ref else "no verdict_ref")

    charter = {}
    if (root / "charter.yaml").exists():
        charter = yaml.safe_load((root / "charter.yaml").read_text(encoding="utf-8")) or {}
    slices = {s.get("id"): s for s in meta.get("slices") or [] if isinstance(s, dict)}

    for c in _criteria(spec):
        cid = str(c.get("id", "?"))
        traces = [t for t in c.get("trace") or [] if isinstance(t, dict)]
        # C04: at least one trace.
        if not traces and not meta.get("legacy"):
            err("C04", cid, "no trace entries")
        for t in traces:
            ref = str(t.get("ref") or "")
            # C05: the ref resolves to a committed file, never a raw signal copy.
            path = _ledger.resolve(root, docs, ref) if ref else None
            if not ref:
                err("C05", cid, "trace entry has no `ref`")
            elif "/raw/" in ref or ref.startswith("raw/"):
                err("C05", cid, f"`{ref}` points into a raw signal copy")
            elif path is None:
                ext = _ledger.external(root, ref)
                if ext and ext[0] == "url":
                    warn("C05", cid, f"`{ref}` is in a repo only known by URL ({ext[1]}); can't check it from here")
                elif ext:
                    err("C05", cid, f"`{ref}` isn't a file in the `{_ledger.ref_id(ref).split('/')[0]}` repo")
                else:
                    err("C05", cid, f"`{ref}` doesn't resolve to a file in this repo or a configured one")
            # C06: the quote appears verbatim in the source.
            if t.get("quote") and path is not None:
                if _norm(str(t["quote"])) not in _norm(path.read_text(encoding="utf-8", errors="replace")):
                    shown = path.relative_to(root).as_posix() if path.is_relative_to(root) else str(path)
                    err("C06", cid, f"quote not found verbatim in {shown}")
            # C23: basis and its required field.
            basis = t.get("basis")
            if basis not in BASES:
                err("C23", cid, f"trace to `{ref}` has basis `{basis}`; use one of {', '.join(BASES)}")
            elif BASES[basis] and not t.get(BASES[basis]):
                err("C23", cid, f"`{basis}` trace to `{ref}` needs `{BASES[basis]}`")
            elif basis == "inferred" and not _assumption_exists(str(t["assumption"]), spec, thread):
                err("C23", cid, f"assumption `{t['assumption']}` isn't on the Thread or in the Review Brief")
        if traces and all(t.get("basis") == "inferred" for t in traces):
            warn("C23", cid, "every trace is inferred")
        # C07: modality allowed by the charter.
        if charter.get("ui_presence") is False and c.get("modality") in ("web", "mobile"):
            err("C07", cid, f"`{c.get('modality')}` criterion, but the charter says ui_presence: false")
        # C08: binary criteria carry no vague terms.
        if c.get("type", "binary") == "binary":
            hits = [w for w in VAGUE if re.search(rf"\b{re.escape(w)}\b", str(c.get("text", "")), re.I)]
            if hits:
                err("C08", cid, f"vague term(s): {', '.join(hits)}")
            if any(re.search(p, str(c.get("text", "")), re.I) for p in EITHER_OR):
                err("C08", cid, "either/or wording; pick one outcome or split into two criteria")
        # C09: threshold criteria are complete.
        if c.get("type") == "threshold":
            th = c.get("threshold") if isinstance(c.get("threshold"), dict) else c
            missing = [k for k in ("metric", "operator", "value", "unit") if th.get(k) in (None, "")]
            if missing:
                err("C09", cid, f"threshold missing {', '.join(missing)}")
            elif not isinstance(th.get("value"), (int, float)):
                err("C09", cid, "threshold value isn't a number")
        # C21: every criterion belongs to a real slice.
        if c.get("slice") not in slices:
            err("C21", cid, f"slice `{c.get('slice')}` isn't in `slices`")

    # C10: required sections are non-empty.
    sections = meta.get("sections") if isinstance(meta.get("sections"), dict) else {}
    for s in SECTIONS:
        if not sections.get(s):
            err("C10", s, f"section `{s}` is empty (write `n/a: <reason>` if it truly doesn't apply)")

    # C20: open questions are answered, deferred with reason and owner, or out of scope.
    for i, q in enumerate(meta.get("open_questions") or [], 1):
        q = q if isinstance(q, dict) else {"text": str(q)}
        where = f"open_questions[{i}]"
        if q.get("status") not in QUESTION_STATUSES:
            err("C20", where, f"status `{q.get('status')}`; use answered, deferred or out_of_scope")
        elif q["status"] == "deferred" and not (q.get("reason") and q.get("owner")):
            err("C20", where, "deferred without a reason and owner")

    # C21: every slice has a criterion, an order and a verify note.
    used = {c.get("slice") for c in _criteria(spec)}
    for sid, s in slices.items():
        if sid not in used:
            err("C21", str(sid), "slice has no criteria")
        if s.get("order") is None:
            err("C21", str(sid), "slice has no `order`")
        if not s.get("verify"):
            err("C21", str(sid), "slice has no `verify` note")
    return out


def _assumption_exists(aid: str, spec: _ledger.Doc, thread: _ledger.Doc | None) -> bool:
    brief = spec.meta.get("review_brief") or {}
    if any(isinstance(a, dict) and str(a.get("id")) == aid for a in brief.get("assumptions") or []):
        return True
    text = thread.path.read_text(encoding="utf-8", errors="replace") if thread else ""
    return re.search(rf"\b{re.escape(aid)}\b", text) is not None


def errors(findings: list[Finding]) -> list[Finding]:
    return [f for f in findings if f.severity == "Error"]


def report_markdown(spec_id: str, findings: list[Finding]) -> str:
    """The mechanical rows, ready for check-spec to paste into the compile report."""
    lines = [f"Mechanical checks for {spec_id} (`cairn check`):", "", "| Rule | Result | Where | Detail |",
             "|---|---|---|---|"]
    for rule in MECHANICAL:
        hits = [f for f in findings if f.rule == rule]
        if not hits:
            lines.append(f"| {rule} | Pass | | |")
        for f in hits:
            lines.append(f"| {rule} | {'Fail' if f.severity == 'Error' else 'Warn'} | {f.where} | {f.message} |")
    return "\n".join(lines) + "\n"
