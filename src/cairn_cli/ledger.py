"""Read-only view over signals/, threads/, and specs/: what was asked, and what went to engineering.

No index or database. Every call rescans the Markdown files, which stays fast at product-repo scale.
"""
from __future__ import annotations

import datetime as _dt
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import yaml

STAGES = ["Exploring", "Framing", "Validating"]  # fidelity order; a Thread's last stage hands off to a Spec
STATUSES = ["Active", "Parked", "Rejected", "Specified", "Handed off"]
# Threads written before stage/status existed carry a single `state`; read it as (stage, status).
LEGACY_STATES = {
    "Signal": ("Exploring", "Active"),
    "Shape": ("Exploring", "Active"),
    "Feasibility": ("Framing", "Active"),
    "Contract": ("Validating", "Handed off"),
    "Launched": ("Validating", "Handed off"),
    "Parked": (None, "Parked"),
    "Rejected": (None, "Rejected"),
}
REFERENCE_KINDS = {"library", "architecture"}


@dataclass
class Doc:
    kind: str  # signal | thread | spec | journey | library | architecture
    id: str
    path: Path
    meta: dict
    body: str
    links: set[str] = field(default_factory=set)  # ids of related docs
    broken: list[str] = field(default_factory=list)  # refs that should resolve to a file here but don't
    updated: str = ""  # date of last commit touching the file, or today if uncommitted

    @property
    def restricted(self) -> bool:
        return str(self.meta.get("data_class", "")).lower() == "restricted"


def _split(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            try:
                return yaml.safe_load(parts[1]) or {}, parts[2]
            except yaml.YAMLError:
                pass
    return {}, text


def ref_id(ref: str) -> str:
    """'feedback:ZD-88421' -> 'ZD-88421'; anchors like 'lib:x#y' keep the part before '#'."""
    return str(ref).split(":", 1)[-1].split("#", 1)[0].strip()


_ref_id = ref_id


def _lookup(docs: dict, ref: str) -> str | None:
    """The doc id a ref names, also accepting path forms like 'backend-api/overview.md'."""
    t = ref_id(ref)
    for cand in (t, t.removesuffix(".md")):
        if cand in docs:
            return cand
        for folder in ("signals", "threads", "specs", "journeys", *sorted(REFERENCE_KINDS)):
            if cand.startswith(folder + "/"):
                rest = cand[len(folder) + 1:]
                if rest in docs or rest.rsplit("/", 1)[-1] in docs:
                    return rest if rest in docs else rest.rsplit("/", 1)[-1]
    return None


def resolve(root: Path, docs: dict, ref: str) -> Path | None:
    """The file a ref points at: a known doc, or any file in the repo by path. None if neither."""
    hit = _lookup(docs, ref)
    if hit:
        return docs[hit].path
    p = root / ref_id(ref)
    return p if p.is_file() else None


def load(root: Path) -> dict[str, Doc]:
    docs: dict[str, Doc] = {}
    for kind, folder, key in (("signal", "signals", "signal_id"),
                              ("thread", "threads", "thread_id"),
                              ("spec", "specs", "spec_id"),
                              ("journey", "journeys", "journey_id")):
        base = root / folder
        if not base.is_dir():
            continue
        for p in sorted(base.rglob("*.md")):
            if "raw" in p.relative_to(base).parts:
                continue  # never surface raw, unredacted copies
            if p.name.endswith(".compile_report.md"):
                continue  # check-spec output, not a Spec
            meta, body = _split(p)
            doc_id = str(meta.get(key) or p.stem)
            docs[doc_id] = Doc(kind, doc_id, p, meta, body)
    # Reference docs are keyed by path under their folder, matching refs like lib:compliance/sec-04.
    for kind in sorted(REFERENCE_KINDS):
        base = root / kind
        if base.is_dir():
            for p in sorted(base.rglob("*.md")):
                meta, body = _split(p)
                doc_id = p.relative_to(base).with_suffix("").as_posix()
                docs[doc_id] = Doc(kind, doc_id, p, meta, body)

    # Wire signal <-> thread <-> spec links in both directions.
    # Required refs must resolve here; outbound refs (Jira etc.) and touches may point outside the repo.
    for d in list(docs.values()):
        required: list[str] = []
        optional: list[str] = []
        if d.kind == "thread":
            required += (d.meta.get("inbound_refs") or []) + (d.meta.get("signal_refs") or [])
            optional += d.meta.get("outbound_refs") or []
            optional += [f"{t}/overview" for t in d.meta.get("touches") or []]
            optional += d.meta.get("bundled_with") or []
            optional += [d.meta["see_thread"]] if d.meta.get("see_thread") else []
        elif d.kind == "spec":
            if d.meta.get("thread_id"):
                required.append(str(d.meta["thread_id"]))
            for c in d.meta.get("criteria") or []:
                required += [t["ref"] for t in (c.get("trace") or []) if isinstance(t, dict) and t.get("ref")]
        for ref in required + optional:
            t = _lookup(docs, ref)
            if t:
                d.links.add(t)
                docs[t].links.add(d.id)
            elif ref in required and not (root / ref_id(ref)).is_file() and str(ref) not in d.broken:
                d.broken.append(str(ref))

    dates = _git_dates(root)
    today = _dt.date.today().isoformat()
    for d in docs.values():
        d.updated = dates.get(d.path.relative_to(root).as_posix(), today)
    return docs


def _git_dates(root: Path) -> dict[str, str]:
    """Last commit date per file, from one git call. Empty outside a git repo."""
    try:
        out = subprocess.run(["git", "log", "--format=@%cs", "--name-only", "--", "signals", "threads",
                              "specs", "journeys", "library", "architecture"],
                             cwd=root, capture_output=True, text=True, timeout=30).stdout
    except (OSError, subprocess.SubprocessError):
        return {}
    dates: dict[str, str] = {}
    date = ""
    for line in out.splitlines():
        if line.startswith("@"):
            date = line[1:]
        elif line and line not in dates:
            dates[line] = date  # log is newest first, so the first date seen is the latest
    try:  # files edited since the last commit count as changed today
        dirty = subprocess.run(["git", "status", "--porcelain"], cwd=root, capture_output=True,
                               text=True, timeout=30).stdout
        for line in dirty.splitlines():
            dates.pop(line[3:].strip(), None)
    except (OSError, subprocess.SubprocessError):
        pass
    return dates


def visible(docs: dict[str, Doc], include_restricted: bool) -> dict[str, Doc]:
    """Drop restricted docs, and links to them, for output that may leave the PM's machine."""
    if include_restricted:
        return docs
    hidden = {i for i, d in docs.items() if d.restricted}
    out = {}
    for i, d in docs.items():
        if i not in hidden:
            # Also scrub hidden ids from ref lists, so a search can't confirm a restricted ticket exists.
            meta = {k: [r for r in v if _ref_id(r) not in hidden] if isinstance(v, list) else v
                    for k, v in d.meta.items()}
            out[i] = Doc(d.kind, d.id, d.path, meta, d.body, d.links - hidden, d.broken, d.updated)
    return out


def stage_status(meta: dict) -> tuple[str | None, str]:
    """A Thread's (stage, status), falling back to the legacy single `state` field."""
    stage, status = meta.get("stage"), meta.get("status")
    if not stage and not status and meta.get("state"):
        stage, status = LEGACY_STATES.get(str(meta["state"]), (str(meta["state"]), None))
    return (str(stage) if stage else None), str(status or "Active")


def thread_label(meta: dict) -> str:
    """One word for tables: the stage while Active, else the status (with the stage it stopped at)."""
    stage, status = stage_status(meta)
    if status == "Active":
        return stage or "?"
    return f"{status} ({stage})" if stage and status in ("Parked", "Rejected") else status


def thread_state(doc: Doc, docs: dict[str, Doc]) -> str:
    if doc.kind in REFERENCE_KINDS:
        return "-"
    if doc.kind == "thread":
        return thread_label(doc.meta)
    threads = [docs[l] for l in doc.links if docs[l].kind == "thread"]
    return ", ".join(sorted({thread_label(t.meta) for t in threads})) or "no thread"


def search(docs: dict[str, Doc], query: str, kind: str | None = None, limit: int = 10) -> list[tuple[int, Doc]]:
    terms = [t for t in re.findall(r"\w+", query.lower()) if len(t) > 1]
    scored = []
    for d in docs.values():
        if kind and d.kind != kind:
            continue
        hay = (d.id + " " + yaml.safe_dump(d.meta, sort_keys=False) + " " + d.body).lower()
        score = sum(hay.count(t) for t in terms)
        if query.strip().lower() == d.id.lower():
            score += 100
        if score:
            scored.append((score, d))
    scored.sort(key=lambda x: (-x[0], x[1].id))
    return scored[:limit]


def lineage(docs: dict[str, Doc], doc_id: str) -> list[Doc]:
    """Everything connected to doc_id: its signals, threads, and specs."""
    seen, stack = [], [doc_id]
    while stack:
        cur = stack.pop()
        if cur in seen or cur not in docs:
            continue
        seen.append(cur)
        # Reference docs are shared by many Threads: list them, but only walk through the one asked about.
        if docs[cur].kind not in REFERENCE_KINDS or cur == doc_id:
            stack.extend(sorted(docs[cur].links))
    order = {"signal": 0, "thread": 1, "spec": 2, "journey": 3, "library": 4, "architecture": 5}
    return sorted((docs[i] for i in seen), key=lambda d: (order[d.kind], d.id))


def snippet(doc: Doc, width: int = 90) -> str:
    text = " ".join(doc.body.split())
    return text[:width] + ("…" if len(text) > width else "")


def as_dict(doc: Doc, docs: dict[str, Doc], root: Path) -> dict:
    """Compact, stable shape for --json output."""
    out = {"id": doc.id, "kind": doc.kind, "path": doc.path.relative_to(root).as_posix(),
           "state": thread_state(doc, docs) if doc.kind in ("signal", "thread", "spec") else None,
           "updated": doc.updated, "links": sorted(doc.links)}
    if doc.kind == "thread":
        out["stage"], out["status"] = stage_status(doc.meta)
        kb = last_kickback(doc.meta)
        if kb:
            out["kickback_category"] = kb.get("category")
    if doc.broken:
        out["broken_refs"] = doc.broken
    for k in ("type", "revision", "spec_status", "owner", "readiness",
              "bundle", "pickup_when", "reject_category"):
        if doc.meta.get(k) is not None:
            out[k] = doc.meta[k]
    return out


def last_kickback(thread_meta: dict, spec_id: str | None = None) -> dict | None:
    """The newest kickback (for one Spec, if given), from `kickbacks` or the older flat keys."""
    entries = [k for k in thread_meta.get("kickbacks") or [] if isinstance(k, dict)]
    if not entries and thread_meta.get("kickback_reason"):
        entries = [{"reason": thread_meta["kickback_reason"], "category": thread_meta.get("kickback_category")}]
    if spec_id:
        entries = [k for k in entries if k.get("spec_id") in (None, spec_id)]
    return entries[-1] if entries else None


def sent(docs: dict[str, Doc]) -> list[Doc]:
    """Specs that went out: spec_status handed_off, or (one-Spec Threads) a Handed-off parent Thread."""
    return [s for s in docs.values() if s.kind == "spec" and (
        s.meta.get("spec_status") == "handed_off" or (s.meta.get("spec_status") is None and any(
            docs[l].kind == "thread" and stage_status(docs[l].meta)[1] == "Handed off" for l in s.links)))]


def snapshot(docs: dict[str, Doc], root: Path) -> dict:
    """The full ledger as plain data: what --json prints and what STATUS.json holds."""
    shipped = {d.id for d in sent(docs)}
    by = lambda k: [as_dict(d, docs, root) for d in docs.values() if d.kind == k]
    return {
        "signals": by("signal"),
        "threads": by("thread"),
        "specs": [dict(x, sent=x["id"] in shipped) for x in by("spec")],
        "reference": [as_dict(d, docs, root) for d in docs.values() if d.kind in REFERENCE_KINDS],
        "broken_refs": {d.id: d.broken for d in docs.values() if d.broken},
    }


def status_markdown(snap: dict) -> str:
    """Short human-readable status page built from snapshot()."""
    lines = ["# Status", "", "Generated by `cairn snapshot`. Do not edit by hand.", ""]
    states: dict[str, int] = {}
    for t in snap["threads"]:
        states[t["state"]] = states.get(t["state"], 0) + 1
    loose = [s for s in snap["signals"] if s["state"] == "no thread"]
    lines.append(f"**{len(snap['signals'])} asks**, {len(loose)} not yet picked up. **Threads:** "
                 + (", ".join(f"{n} {k}" for k, n in sorted(states.items())) or "none") + ".")
    lines += ["", "## Threads", "", "| Thread | Stage | Updated | Signals | Specs |", "|---|---|---|---|---|"]
    ids = {x["id"]: x for x in snap["signals"] + snap["specs"]}
    for t in snap["threads"]:
        sig = ", ".join(l for l in t["links"] if ids.get(l, {}).get("kind") == "signal") or "-"
        spc = ", ".join(l for l in t["links"] if ids.get(l, {}).get("kind") == "spec") or "-"
        lines.append(f"| {t['id']} | {t['state']} | {t['updated']} | {sig} | {spc} |")
    lines += ["", "## Sent to engineering", ""]
    sent_specs = [s for s in snap["specs"] if s["sent"]]
    lines += [f"- {s['id']} rev {s.get('revision', 1)} (updated {s['updated']})" for s in sent_specs] or ["- nothing yet"]
    parked = [t for t in snap["threads"] if t["status"] == "Parked"]
    if parked:
        lines += ["", "## Parked: waiting on", ""]
        lines += [f"- {t['id']}: {t.get('pickup_when', 'unknown')}" for t in parked]
    if loose:
        lines += ["", "## Asks with no Thread yet", ""]
        lines += [f"- {s['id']} ({s.get('type', '?')}, {s['updated']})" for s in loose]
    if snap["broken_refs"]:
        lines += ["", "## Broken references", ""]
        lines += [f"- {k}: {', '.join(v)}" for k, v in snap["broken_refs"].items()]
    return "\n".join(lines) + "\n"
