#!/usr/bin/env python3
"""Build the audit viewer from the findings register.

Usage:  python3 -I build_viewer.py [--dir <audit folder>]      (default: the folder this script sits in)
Output: <audit folder>/index.html                (local; open directly in a browser)
        <audit folder>/audit-viewer-shared.html  (redacted, document skeleton stripped: publish this one)

Inputs, all inside the audit folder:
  data/audit.json      product name, projects, streams, reference list, aliases, redactions, audit runs
  data/findings.json   every finding with its current status and history (the source of truth)
  data/blockers.json   every launch blocker with its current status and history
  <project>/launch-readiness.md   current verdict per project; `<!-- blockers:<project> -->` marks the blocker table
  reference/**.md, README.md      charters, CLAUDE.md proposals, architecture wiki
  history/**                      original reports; only their scope/method notes appear, on the stream pages
"""
import argparse
import json
import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Sections of a stream report or re-check file that the stream page's table already shows.
DROP_REPORT = re.compile(r"^(findings|detail|verification|summary$)", re.I)
DROP_RECHECK = re.compile(r"^(launch-blocker findings|status of all findings|new findings|verification|"
                          r"connector blockers|blocker status|claude\.md proposals)", re.I)


def sections(md: str) -> list[tuple[str, str]]:
    """Split Markdown on '## ' headings into (heading, text including the heading line)."""
    out: list[tuple[str, list[str]]] = [("", [])]
    for line in md.splitlines():
        if line.startswith("## "):
            out.append((line[3:].strip(), [line]))
        else:
            out[-1][1].append(line)
    return [(h, "\n".join(lines)) for h, lines in out]


def title_of(text: str, fallback: str) -> str:
    match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    return match.group(1).strip() if match else fallback


def date_label(path: str) -> str:
    match = re.search(r"(\d{4})-(\d{2})-(\d{2})", path)
    return f"{int(match.group(3))} {MONTHS[int(match.group(2)) - 1]}" if match else "re-check"


def stream_notes(root: pathlib.Path, stream: dict) -> str:
    """Scope, method and appendices for a stream page: the report minus what the table now shows."""
    notes: list[str] = []
    kept: list[str] = []
    report = root / stream["report"] if stream.get("report") else None
    if report and report.exists():
        parts = sections(report.read_text(encoding="utf-8"))
        notes.append(re.sub(r"^#\s+.*\n?", "", parts[0][1], count=1).strip())
        kept = [text for head, text in parts[1:] if not DROP_REPORT.match(head)]
    extras: list[str] = []
    for rel in stream.get("recheckNotes") or []:
        path = root / rel
        if not path.exists():
            continue
        label = date_label(rel)
        for head, text in sections(path.read_text(encoding="utf-8"))[1:]:
            if not DROP_RECHECK.match(head):
                extras.append(text.replace("## ", f"## ({label}) ", 1))
    if any(re.match(r"^## \([^)]*\) appendix", e, re.I) for e in extras):
        kept = [k for k in kept if not re.match(r"^## appendix", k, re.I)]
    return "\n\n".join([*notes, *kept, *extras]).strip()


def build(root: pathlib.Path) -> None:
    config = json.loads((root / "data/audit.json").read_text(encoding="utf-8"))
    findings = json.loads((root / "data/findings.json").read_text(encoding="utf-8"))["findings"]
    blockers_path = root / "data/blockers.json"
    blockers = json.loads(blockers_path.read_text(encoding="utf-8"))["blockers"] if blockers_path.exists() else []
    old_ids = config.get("oldIds", {})

    aliases = dict(config.get("aliases", {}))
    streams = []
    for s in config["streams"]:
        route = f"stream/{s['key']}"
        for rel in [s.get("report"), *(s.get("recheckNotes") or [])]:
            if rel:
                aliases.setdefault(rel, route)
        streams.append({**s, "notes": stream_notes(root, s), "notesOldId": old_ids.get(s.get("report", ""), s.get("report", ""))})

    docs = []
    for path in sorted((root / "reference").rglob("*.md")) if (root / "reference").exists() else []:
        rel = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8")
        old = old_ids.get(rel, rel)
        aliases.setdefault(old, f"doc/{rel}")
        aliases[rel] = f"doc/{rel}"
        docs.append({"id": rel, "oldId": old, "title": title_of(text, rel), "md": text})
    if (root / "README.md").exists():
        docs.append({"id": "README.md", "oldId": "README.md", "title": "About this audit",
                     "md": (root / "README.md").read_text(encoding="utf-8")})
        aliases["README.md"] = "doc/README.md"

    readiness = {}
    for project in config["projects"]:
        rel = f"{project['key']}/launch-readiness.md"
        path = root / rel
        md = path.read_text(encoding="utf-8") if path.exists() else (
            f"# {project['label']} launch readiness\n\n## Recommendation: **PENDING**\n\n<!-- blockers:{project['key']} -->\n")
        readiness[project["key"]] = {"id": rel, "md": md}
        aliases[rel] = f"readiness/{project['key']}"

    view_config = {
        "product": config["product"], "root": config.get("root", "docs/PRODUCTION-AUDIT"),
        "projects": config["projects"], "reference": config.get("reference", []),
        "wikiRoot": config.get("wikiRoot", ""),
    }
    payload = json.dumps(
        {"config": view_config, "updated": config["updated"], "audits": config.get("audits", []),
         "streams": streams, "findings": findings, "blockers": blockers, "readiness": readiness,
         "docs": docs, "aliases": aliases},
        ensure_ascii=False,
    ).replace("<", "\\u003c")  # no raw '<' in the data: it can't close the <script>, and to_artifact can't touch it

    template = root / "viewer-template.html"
    if not template.exists():
        template = HERE.parent / "assets" / "viewer-template.html"
    html = template.read_text(encoding="utf-8").replace("__AUDIT_DATA__", payload)
    (root / "index.html").write_text(html, encoding="utf-8")
    print(f"wrote index.html: {len(findings)} findings, {len(blockers)} blockers, {len(streams)} streams, "
          f"{len(docs)} reference docs")

    shared = to_artifact(redact(html, config.get("redact", [])))
    (root / "audit-viewer-shared.html").write_text(shared, encoding="utf-8")
    leaks = [lit for lit, _ in config.get("redact", []) if lit in shared]
    print("wrote audit-viewer-shared.html (redacted, artifact skeleton)" + (f"; STILL CONTAINS {leaks}" if leaks else ""))


def redact(html: str, rules: list) -> str:
    for secret, label in rules:
        html = html.replace(secret, label)
    return html


def to_artifact(html: str) -> str:
    """Strip the document skeleton: an artifact host supplies doctype, html, head and body."""
    for pattern in (
        r"<!doctype html>\s*",
        r"<html[^>]*>\s*",
        r"</?head>\s*",
        r"<body>\s*",
        r"</body>\s*",
        r"</html>\s*",
        r'<meta charset="utf-8">\s*',
        r'<meta name="viewport"[^>]*>\s*',
    ):
        html = re.sub(pattern, "", html, flags=re.IGNORECASE)
    return html.replace("</title>", '</title>\n<meta name="claude:viewport-fit-sides" content="cover">', 1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dir", default=str(HERE), help="audit folder (default: this script's folder)")
    build(pathlib.Path(parser.parse_args().dir).resolve())
