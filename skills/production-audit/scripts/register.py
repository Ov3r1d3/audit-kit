#!/usr/bin/env python3
"""Maintain the audit's findings register (data/findings.json, data/blockers.json, data/audit.json).

  init     <dir> --product NAME [--project key:Label:Sub:LB ...]   scaffold a new audit folder
  ingest   <dir> --project KEY --date YYYY-MM-DD --reports <folder> add a first audit's stream reports + blockers
  recheck  <dir> --date YYYY-MM-DD --checks <folder>                apply a re-audit's status files
  set      <dir> ID --status S [--evidence ..] [--note ..] [--date ..]   record one status change by hand
  status   <dir> [--project KEY]                                     print counts (for writing the verdict)
  validate <dir>                                                     check the register is complete and consistent

Report formats are defined in references/formats.md. Run with: python3 -I register.py <command> ...
"""
import argparse
import datetime
import json
import pathlib
import re
import shutil
import sys
from collections import Counter

SKILL = pathlib.Path(__file__).resolve().parent.parent
SEVS = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
STATUSES = ["NOT-VERIFIABLE", "REGRESSED", "ACCEPTED", "PARTIAL", "FIXED", "OPEN"]
ID_PAT = r"[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*-[A-Z]?\d+[a-z]?"
ID_RE = re.compile(rf"^{ID_PAT}$")


# ---------------------------------------------------------------- markdown tables
def sections(md):
    out, head, buf = [], "", []
    for line in md.splitlines():
        if line.startswith("## "):
            out.append((head, "\n".join(buf)))
            head, buf = line[3:].strip(), []
        else:
            buf.append(line)
    out.append((head, "\n".join(buf)))
    return out


def cells(line):
    s = line.strip()
    if not s.startswith("|"):
        return None
    s = s[1:-1] if s.endswith("|") else s[1:]
    parts, cur, tick, i = [], "", False, 0
    while i < len(s):
        ch = s[i]
        if ch == "\\" and i + 1 < len(s) and s[i + 1] == "|":
            cur += "|"; i += 2; continue
        if ch == "`":
            tick = not tick
        if ch == "|" and not tick:
            parts.append(cur.strip()); cur = ""
        else:
            cur += ch
        i += 1
    parts.append(cur.strip())
    return parts


def rows(body):
    """Yield (header, cells, id) for every table row whose first cell is a finding/blocker ID."""
    header = None
    for line in body.splitlines():
        c = cells(line)
        if c is None:
            header = None
            continue
        if header is None:
            header = [h.strip("* ").lower() for h in c]
            continue
        if set("".join(c)) <= set("-: "):
            continue
        rid = c[0].strip("*` ")
        if ID_RE.match(rid):
            yield header, c, rid


def col(header, row, *names):
    for n in names:
        for i, h in enumerate(header):
            if h.startswith(n) and i < len(row):
                return row[i]
    return ""


def norm_sev(v):
    v = v.strip("* ").upper()
    return next((s for s in SEVS if v.startswith(s)), "")


def norm_status(v):
    u = re.sub(r"[*`]", "", v).strip().upper().replace("NOT VERIFIABLE", "NOT-VERIFIABLE")
    return next((s for s in STATUSES if u.startswith(s)), "")


def details(md):
    """finding id -> detail markdown, from '### ...ID...' headings inside '## Detail...' sections."""
    out = {}
    for head, body in sections(md):
        if not head.lower().startswith("detail"):
            continue
        cur, buf = None, []
        for line in body.splitlines() + ["### END"]:
            m = re.match(r"^###\s+(.*)$", line)
            if m:
                for fid in cur or []:
                    out.setdefault(fid, "\n".join(buf).strip())
                cur, buf = re.findall(ID_PAT, m.group(1)), []
            elif cur is not None:
                buf.append(line)
    return out


# ---------------------------------------------------------------- register io
def load(root):
    cfg = json.loads((root / "data/audit.json").read_text())
    fnd = json.loads((root / "data/findings.json").read_text())
    blk = json.loads((root / "data/blockers.json").read_text())
    return cfg, fnd, blk


def save(root, cfg, fnd, blk):
    order = {s["key"]: i for i, s in enumerate(cfg["streams"])}
    fnd["findings"].sort(key=lambda f: (order.get(f["stream"], 99), SEVS.index(f["severity"]), f["id"]))
    porder = {p["key"]: i for i, p in enumerate(cfg["projects"])}
    blk["blockers"].sort(key=lambda b: (porder.get(b["project"], 99), int(re.sub(r"\D", "", b["id"]) or 0)))
    for name, obj in (("audit", cfg), ("findings", fnd), ("blockers", blk)):
        (root / f"data/{name}.json").write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n")


def stream_for(cfg, fid):
    best = None
    for s in cfg["streams"]:
        for p in s.get("prefixes", []):
            if fid.startswith(p + "-") and (best is None or len(p) > len(best[1])):
                best = (s, p)
    return best[0] if best else None


def new_finding(cfg, header, row, fid, date, stream, detail=""):
    return {
        "id": fid, "project": stream["project"], "stream": stream["key"],
        "severity": norm_sev(col(header, row, "severity", "sev")),
        "blocker": col(header, row, "launch blocker", "lb").strip("* ").upper().startswith("Y"),
        "owasp": col(header, row, "owasp"), "wcag": col(header, row, "wcag"),
        "location": col(header, row, "file"), "description": col(header, row, "description"),
        "fix": col(header, row, "suggested fix", "fix"), "effort": col(header, row, "effort"),
        "found": date, "status": "OPEN", "since": date, "evidence": "", "note": "",
        "history": [{"date": date, "status": "OPEN", "note": "Found."}], "detail": detail,
    }


def new_blocker(project, header, row, bid, date):
    return {
        "id": bid, "project": project, "severity": norm_sev(col(header, row, "severity", "sev")),
        "title": col(header, row, "blocker", "root cause", "title"), "sources": col(header, row, "source"),
        "fix": col(header, row, "one-line fix", "fix"), "effort": col(header, row, "effort"),
        "tier": col(header, row, "tier"), "found": date, "status": "OPEN", "since": date,
        "evidence": "", "remains": "", "history": [{"date": date, "status": "OPEN", "note": "Raised."}],
    }


def apply_status(rec, status, date, note, evidence=None, remains=None):
    if evidence is not None:
        rec["evidence"] = evidence
    if remains is not None:
        rec["remains"] = remains
    if "note" in rec:
        rec["note"] = note
    if status != rec["status"]:
        rec["status"], rec["since"] = status, date
    rec["history"] = [h for h in rec["history"] if h["date"] != date or h["note"] == "Found."] + [
        {"date": date, "status": status, "note": note or "Re-checked."}]


def touch(cfg, date, scope):
    cfg["updated"] = max(cfg.get("updated", ""), date)
    runs = cfg.setdefault("audits", [])
    if not any(a["date"] == date and a["scope"] == scope for a in runs):
        runs.append({"date": date, "scope": scope})
    runs.sort(key=lambda a: a["date"])


# ---------------------------------------------------------------- commands
def cmd_init(a):
    root = pathlib.Path(a.dir).resolve()
    for d in ("data", "reference/architecture", "history"):
        (root / d).mkdir(parents=True, exist_ok=True)
    projects = []
    for spec in a.project or ["platform:Platform::LB"]:
        key, label, sub, prefix = (spec.split(":") + ["", "", "", ""])[:4]
        projects.append({"key": key, "label": label or key.title(), "sub": sub, "blockerPrefix": prefix or "LB"})
        (root / key).mkdir(exist_ok=True)
    cfg_path = root / "data/audit.json"
    if not cfg_path.exists():
        cfg = {"product": a.product, "root": a.root, "updated": "", "audits": [], "projects": projects,
               "streams": [], "reference": [["README.md", "About this audit"]], "wikiRoot": "",
               "aliases": {}, "oldIds": {}, "redact": []}
        cfg_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=1) + "\n")
        (root / "data/findings.json").write_text('{\n "findings": []\n}\n')
        (root / "data/blockers.json").write_text('{\n "blockers": []\n}\n')
    shutil.copy(SKILL / "scripts/build_viewer.py", root / "build-viewer.py")
    shutil.copy(SKILL / "assets/viewer-template.html", root / "viewer-template.html")
    if not (root / "README.md").exists():
        (root / "README.md").write_text((SKILL / "assets/README.md").read_text().replace("{{PRODUCT}}", a.product))
    print(f"initialised {root}")


def cmd_ingest(a):
    root = pathlib.Path(a.dir).resolve()
    cfg, fnd, blk = load(root)
    project = next(p for p in cfg["projects"] if p["key"] == a.project)
    reports = pathlib.Path(a.reports)
    reports = reports if reports.is_absolute() else root / reports
    have = {f["id"] for f in fnd["findings"]}
    added = Counter()
    for s in [s for s in cfg["streams"] if s["project"] == a.project]:
        path = root / s["report"] if s.get("report") else None
        if not path or not path.exists():
            print(f"  no report for stream {s['key']} ({s.get('report')})", file=sys.stderr)
            continue
        md = path.read_text()
        det = details(md)
        for head, body in sections(md):
            if not head.lower().startswith("findings"):
                continue
            for header, row, fid in rows(body):
                if fid in have or not norm_sev(col(header, row, "severity", "sev")):
                    continue
                owner = stream_for(cfg, fid) or s
                fnd["findings"].append(new_finding(cfg, header, row, fid, a.date, owner, det.get(fid, "")))
                have.add(fid)
                added[owner["key"]] += 1
    bfile = reports / "99-blockers.md"
    nb = 0
    if bfile.exists():
        bhave = {b["id"] for b in blk["blockers"]}
        for header, row, bid in rows(bfile.read_text()):
            if bid.startswith(project["blockerPrefix"] + "-") and bid not in bhave:
                blk["blockers"].append(new_blocker(a.project, header, row, bid, a.date))
                nb += 1
    else:
        print(f"  no {bfile.relative_to(root)}: no blockers ingested", file=sys.stderr)
    touch(cfg, a.date, a.scope or f"{project['label']}: audit, {sum(added.values())} findings")
    save(root, cfg, fnd, blk)
    print(f"ingested {sum(added.values())} findings ({dict(added)}) and {nb} blockers")


def cmd_recheck(a):
    root = pathlib.Path(a.dir).resolve()
    cfg, fnd, blk = load(root)
    checks = pathlib.Path(a.checks)
    checks = checks if checks.is_absolute() else root / checks
    byid = {f["id"]: f for f in fnd["findings"]}
    bbyid = {b["id"]: b for b in blk["blockers"]}
    streams = {s["key"]: s for s in cfg["streams"]}
    changed, new, unknown = Counter(), 0, []
    for path in sorted(checks.glob("*.md")):
        rel = path.relative_to(root).as_posix()
        md = path.read_text()
        key = path.stem.removesuffix("-status")
        if key in streams:
            notes = streams[key].setdefault("recheckNotes", [])
            if rel not in notes:
                notes.append(rel)
        for head, body in sections(md):
            h = head.lower()
            if h.startswith("status of all findings"):
                for header, row, fid in rows(body):
                    st = norm_status(col(header, row, "status"))
                    f = byid.get(fid)
                    if not f or not st:
                        if not f:
                            unknown.append(fid)
                        continue
                    before = f["status"]
                    apply_status(f, st, a.date, col(header, row, "note"), col(header, row, "current evidence", "evidence"))
                    changed[f"{before}->{st}"] += 1
            elif h.startswith("new findings"):
                for header, row, fid in rows(body):
                    s = stream_for(cfg, fid)
                    if fid in byid or not s or not norm_sev(col(header, row, "severity")):
                        if not s:
                            unknown.append(fid)
                        continue
                    byid[fid] = new_finding(cfg, header, row, fid, a.date, s)
                    fnd["findings"].append(byid[fid])
                    new += 1
            elif h.startswith("blocker status"):
                for header, row, bid in rows(body):
                    b = bbyid.get(bid)
                    st = norm_status(col(header, row, "status"))
                    if b and st:
                        apply_status(b, st, a.date, col(header, row, "what remains", "note") or col(header, row, "evidence"),
                                     col(header, row, "evidence", "current evidence"), col(header, row, "what remains"))
            elif h.startswith("new blockers"):
                for header, row, bid in rows(body):
                    proj = next((p["key"] for p in cfg["projects"] if bid.startswith(p["blockerPrefix"] + "-")), None)
                    if proj and bid not in bbyid:
                        bbyid[bid] = new_blocker(proj, header, row, bid, a.date)
                        blk["blockers"].append(bbyid[bid])
    touch(cfg, a.date, a.scope or f"Re-check of every open finding, {new} new")
    save(root, cfg, fnd, blk)
    print(f"status rows applied: {dict(changed)}; new findings: {new}")
    if unknown:
        print(f"unknown or unassignable IDs (check prefixes in audit.json): {sorted(set(unknown))}", file=sys.stderr)


def cmd_set(a):
    root = pathlib.Path(a.dir).resolve()
    cfg, fnd, blk = load(root)
    rec = next((r for r in fnd["findings"] + blk["blockers"] if r["id"] == a.id), None)
    if not rec:
        sys.exit(f"no finding or blocker {a.id}")
    status = norm_status(a.status)
    if not status:
        sys.exit(f"status must be one of {STATUSES}")
    date = a.date or datetime.date.today().isoformat()
    apply_status(rec, status, date, a.note or "", a.evidence)
    cfg["updated"] = max(cfg.get("updated", ""), date)
    save(root, cfg, fnd, blk)
    print(f"{a.id}: {status} since {rec['since']}")


def cmd_status(a):
    root = pathlib.Path(a.dir).resolve()
    cfg, fnd, blk = load(root)
    for p in cfg["projects"]:
        if a.project and p["key"] != a.project:
            continue
        fl = [f for f in fnd["findings"] if f["project"] == p["key"]]
        bl = [b for b in blk["blockers"] if b["project"] == p["key"]]
        print(f"== {p['label']}: {len(fl)} findings, {len(bl)} blockers")
        print("  blockers:", dict(Counter(b["status"] for b in bl)))
        print(f"  {'severity':10}" + "".join(f"{s:>16}" for s in STATUSES))
        for sev in SEVS:
            c = Counter(f["status"] for f in fl if f["severity"] == sev)
            print(f"  {sev:10}" + "".join(f"{c[s]:>16}" for s in STATUSES))
        for s in [s for s in cfg["streams"] if s["project"] == p["key"]]:
            c = Counter(f["status"] for f in fl if f["stream"] == s["key"])
            print(f"  {s['key']:18} total={sum(c.values()):3}  " + " ".join(f"{k.lower()}={v}" for k, v in sorted(c.items())))


def cmd_validate(a):
    root = pathlib.Path(a.dir).resolve()
    cfg, fnd, blk = load(root)
    problems = []
    keys = {s["key"] for s in cfg["streams"]}
    projects = {p["key"] for p in cfg["projects"]}
    ids = Counter(f["id"] for f in fnd["findings"]) + Counter(b["id"] for b in blk["blockers"])
    problems += [f"duplicate id {i}" for i, n in ids.items() if n > 1]
    for f in fnd["findings"]:
        for field in ("severity", "location", "description", "fix", "status", "since"):
            if not f.get(field):
                problems.append(f"{f['id']}: missing {field}")
        if f["stream"] not in keys:
            problems.append(f"{f['id']}: unknown stream {f['stream']}")
        if f["status"] in ("FIXED", "PARTIAL", "ACCEPTED") and not (f.get("evidence") or f.get("note")):
            problems.append(f"{f['id']}: {f['status']} without evidence")
    for b in blk["blockers"]:
        if b["project"] not in projects:
            problems.append(f"{b['id']}: unknown project")
        for field in ("severity", "title", "fix", "status"):
            if not b.get(field):
                problems.append(f"{b['id']}: missing {field}")
    for p in projects:
        if not (root / p / "launch-readiness.md").exists():
            problems.append(f"{p}/launch-readiness.md missing")
        elif f"<!-- blockers:{p} -->" not in (root / p / "launch-readiness.md").read_text():
            problems.append(f"{p}/launch-readiness.md has no <!-- blockers:{p} --> marker")
    for s in cfg["streams"]:
        if s.get("report") and not (root / s["report"]).exists():
            problems.append(f"stream {s['key']}: report {s['report']} missing")
    print("\n".join(problems) if problems else f"ok: {len(fnd['findings'])} findings, {len(blk['blockers'])} blockers")
    sys.exit(1 if problems else 0)


def main():
    ap = argparse.ArgumentParser(description="Audit findings register")
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("init"); p.add_argument("dir"); p.add_argument("--product", required=True)
    p.add_argument("--project", action="append", help="key:Label:Subtitle:BlockerPrefix (repeatable)")
    p.add_argument("--root", default="docs/PRODUCTION-AUDIT", help="path shown in the viewer")
    p = sp.add_parser("ingest"); p.add_argument("dir"); p.add_argument("--project", required=True)
    p.add_argument("--date", required=True); p.add_argument("--reports", required=True); p.add_argument("--scope")
    p = sp.add_parser("recheck"); p.add_argument("dir"); p.add_argument("--date", required=True)
    p.add_argument("--checks", required=True); p.add_argument("--scope")
    p = sp.add_parser("set"); p.add_argument("dir"); p.add_argument("id"); p.add_argument("--status", required=True)
    p.add_argument("--evidence"); p.add_argument("--note"); p.add_argument("--date")
    p = sp.add_parser("status"); p.add_argument("dir"); p.add_argument("--project")
    p = sp.add_parser("validate"); p.add_argument("dir")
    a = ap.parse_args()
    {"init": cmd_init, "ingest": cmd_ingest, "recheck": cmd_recheck, "set": cmd_set,
     "status": cmd_status, "validate": cmd_validate}[a.cmd](a)


if __name__ == "__main__":
    main()
