# Formats

`scripts/register.py` parses these files. **Column names and section headings must match**, or rows are silently skipped. Give this file to every stream agent and every re-check agent.

## Contents
1. Folder layout
2. Stream report (first audit)
3. Blocker draft (`99-blockers.md`)
4. Re-check status file
5. Blocker re-check (`blockers.md`)
6. Register records (`data/*.json`)
7. Launch-readiness page

---

## 1. Folder layout

```
<root>/                                   default docs/PRODUCTION-AUDIT/
  README.md                               from assets/README.md
  build-viewer.py  viewer-template.html   copied in by `register.py init`
  index.html  audit-viewer-shared.html    generated
  data/audit.json  data/findings.json  data/blockers.json
  <project>/launch-readiness.md           one per project (current state, rewritten each run)
  reference/<project>-charter.md
  reference/<project>-claude-md-proposals.md
  reference/architecture/00-README.md …   wiki (primary project)
  reference/<project>-architecture-brief.md   brief (secondary projects)
  history/<YYYY-MM-DD>-<project>-audit/<NN>-<stream>.md   first-audit stream reports
  history/<YYYY-MM-DD>-<project>-audit/99-blockers.md     blocker draft
  history/<YYYY-MM-DD>-recheck/<stream-key>.md            re-check status files
  history/<YYYY-MM-DD>-recheck/blockers.md                blocker re-check
```

## 2. Stream report (first audit)

Path: `history/<date>-<project>-audit/<NN>-<slug>.md`. It must also be registered as the stream's `report` in `data/audit.json`.

```markdown
# <NN> — <Stream title> (Stream <letter>)

| | |
|---|---|
| **Stream** | <letter> — <title> |
| **Agent** | <agent type> |
| **Date** | <YYYY-MM-DD> |
| **Scope** | <dirs / files> |

## What was checked
1. … (numbered; for a stream with zero findings this list is the proof it was not skipped)

## Findings

| ID | Severity | Launch Blocker | File:Line | Description (consequence) | Suggested Fix | Effort |
|---|---|---|---|---|---|---|
| CQB-01 | CRITICAL | Y | `path/File.java:383` | <what breaks, for whom: "a customer who cancels is still billed next month"> | <concrete change> | S |

## Detail — CRITICAL / HIGH
### CQB-01 — <short title>
<evidence excerpt, reproduction (curl / SQL / steps), why the fix works>

## Known / Accepted (still open)
<items already documented in CLAUDE.md etc.: cite them, do not re-raise as findings>

## Verification
<what was re-opened before finishing; commands run>
```

Rules:
- **ID:** `<PREFIX>-<NN>`. The prefix is unique per stream and listed in the stream's `prefixes`. Use the same prefix across runs.
- **Severity:** exactly `CRITICAL`, `HIGH`, `MEDIUM` or `LOW`.
- **Launch Blocker:** `Y` or `N`.
- **Effort:** `S` (≤ 1 day), `M` (2–5 days) or `L` (> 1 week).
- **Optional columns.** `OWASP` (security) and `WCAG` (accessibility) may be added between Launch Blocker and File:Line.
- **No raw `|` inside a cell.** Escape it as `\|`.
- **The parser reads only `## Findings` tables.** Tables elsewhere (inventories, coverage maps) are fine and show up in the stream's notes.
- **Detail sections** are attached to their finding by the ID in the `###` heading.

## 3. Blocker draft (`99-blockers.md`)

Written by the orchestrator in Phase 4 of a first audit. It de-duplicates the `Launch Blocker = Y` rows into root causes.

```markdown
# <Project> launch blockers (<date>)

| ID | Severity | Blocker | Source findings | One-line fix | Effort | Tier |
|---|---|---|---|---|---|---|
| LB-01 | CRITICAL | <root cause, one sentence> | SEC-A-01, DB-01 | <fix> | S | Tier 0 |
```

- The ID prefix is the project's `blockerPrefix` (`LB`, `CB`, …).
- **Source findings** lists finding IDs, comma-separated; the viewer links them both ways.
- **Tiers:** `Tier 0` is ops/config, `Tier 1` is small code, `Tier 2` needs design. More tiers are fine.

## 4. Re-check status file

Path: `history/<date>-recheck/<stream-key>.md`. One file per stream; the file name must be the stream key, so the stream page picks up its notes.

```markdown
# <Stream title> — re-check <YYYY-MM-DD>

<one paragraph: what changed in this area since the last check, and what is still dangerous>

`STATUS-COUNTS: total=N fixed=a partial=b open=c regressed=d accepted=e notverifiable=f`

## Status of all findings

| ID | Orig. severity | Status | Current evidence (file:line) | Note |
|---|---|---|---|---|
| CQB-01 | CRITICAL | FIXED | `BillingJob.java:88` (a1b2c3d) now skips cancelled subscriptions | no E2E test for it yet |

## New findings

| ID | Severity | Launch Blocker | File:Line | Description (consequence) | Suggested Fix | Effort |
|---|---|---|---|---|---|---|
| CQB-R01 | MEDIUM | N | `ImportService.java:122` | … | … | S |

## <anything else worth keeping: refreshed appendices, contrast arithmetic, inventories>

## Verification
```

Rules:
- **Every ID currently in the register for this stream gets a row,** including findings already FIXED. Re-confirm them: a fix can regress.
- **Status values:**

  | Status | Meaning |
  |---|---|
  | `FIXED` | Can no longer happen. Cite the code that proves it. |
  | `PARTIAL` | Improved, but a stated consequence is still reachable. Say what remains. |
  | `OPEN` | Unchanged. Cite the current location. |
  | `REGRESSED` | Worse than before. |
  | `ACCEPTED` | Documented as a deliberate decision. Cite where. |
  | `NOT-VERIFIABLE` | Depends on infra or prod state. Say what would prove it. |

- **Use the column name `Orig. severity` in the status table, never plain `Severity`.**
- **New findings use the stream prefix plus `R` and the next number** (`CQB-R01`). Number past any existing `-R` IDs.
- **Never mark FIXED from a commit message alone.** Read the code.

## 5. Blocker re-check (`blockers.md`)

Written by the orchestrator after the stream files.

```markdown
## Blocker status

| ID | Status | Evidence | What remains |
|---|---|---|---|
| LB-07 | PARTIAL | `d4e5f6a` removed the defaults, but … | `@Validated` on the properties |

## New blockers

| ID | Severity | Blocker | Source findings | One-line fix | Effort | Tier |
|---|---|---|---|---|---|---|
| LB-26 | HIGH | … | OPS-R02 | … | S | Tier 0 |
```

New blockers continue the project's numbering.

## 6. Register records (`data/*.json`)

**`data/audit.json`**

```json
{
 "product": "Acme",
 "root": "docs/PRODUCTION-AUDIT",
 "updated": "2026-10-27",
 "audits": [{"date": "2026-10-21", "scope": "Platform: first audit, 315 findings", "commits": {"acme-api": "cdc8f17"}}],
 "projects": [{"key": "platform", "label": "Platform", "sub": "API · web · E2E", "blockerPrefix": "LB"}],
 "streams": [{"key": "be-code", "project": "platform", "title": "Backend code", "prefixes": ["CQB"],
              "report": "history/2026-10-21-platform-audit/10-code-review.md",
              "recheckNotes": ["history/2026-10-27-recheck/be-code.md"]}],
 "reference": [["README.md", "About this audit"], ["reference/platform-charter.md", "Platform charter"]],
 "wikiRoot": "reference/architecture/00-README.md",
 "aliases": {}, "oldIds": {},
 "redact": [["literal-secret-quoted-in-a-report", "[redacted]"]]
}
```

- **`audits[].commits`** records the HEAD of each repo audited in that run. A re-check diffs from these baselines.
- **`redact`** lists literal secrets or default passwords that reports quote. Only the shared copy is redacted.
- **`aliases` and `oldIds`** are only needed when files were moved after links to them were written.

**Finding**

```json
{"id": "CQB-01", "project": "platform", "stream": "be-code", "severity": "CRITICAL", "blocker": true,
 "owasp": "", "wcag": "", "location": "`File.java:383`", "description": "…", "fix": "…", "effort": "S",
 "found": "2026-10-21", "status": "FIXED", "since": "2026-10-27",
 "evidence": "`File.java:441` (a1b2c3d)", "note": "…",
 "history": [{"date": "2026-10-21", "status": "OPEN", "note": "Found."},
             {"date": "2026-10-27", "status": "FIXED", "note": "…"}],
 "detail": "<markdown from the Detail section>"}
```

**Blocker**: `id, project, severity, title, sources, fix, effort, tier, found, status, since, evidence, remains, history`.

`since` is the date the status last *changed*. An unchanged OPEN finding keeps its `found` date ("Open since 21 Oct").

## 7. Launch-readiness page

`<project>/launch-readiness.md` is rewritten on every run as **current state, never "re-audit of …"**. History lives in the register. Template: `references/readiness-template.md`. It must contain the line `<!-- blockers:<project> -->` where the blocker table goes, and a heading `## Recommendation: **GO**` or `**NO-GO**`; the viewer parses that verdict.
