# About this audit

The pre-production audit of {{PRODUCT}}.

**Every finding has exactly one row, showing its current status.** When a finding is fixed, its row says *Fixed* with the date. There are no separate "re-audit" reports to reconcile: a re-audit updates the rows.

## Layout

| Path | What it is |
|---|---|
| `data/findings.json` | **The findings register: the source of truth.** One record per finding: severity, location, consequence, fix, effort, current `status`, the date it last changed (`since`), and a `history` of every check |
| `data/blockers.json` | The launch blockers, in the same shape |
| `data/audit.json` | Product name, projects, streams, reference pages, redactions, and the list of audit runs |
| `<project>/launch-readiness.md` | Each project's current verdict, questions and order of operations. The blocker table is generated from the register at the `<!-- blockers:<project> -->` marker |
| `reference/` | Charters, CLAUDE.md proposals, the architecture wiki |
| `history/` | The original reports of every audit run, kept for traceability. The viewer shows only their scope and method notes, on the stream pages |
| `build-viewer.py`, `viewer-template.html` | Build the viewer (`index.html`) and the redacted shared copy (`audit-viewer-shared.html`) |

## Statuses

| Status | Meaning | Counted as |
|---|---|---|
| Open | Unchanged | Active |
| Partial | Materially improved, but a stated consequence is still reachable | Active |
| Regressed | Worse than when found | Active |
| Fixed | Can no longer happen; evidence cites the code that proves it | Closed |
| Accepted | Not fixed, but documented as a deliberate decision | Closed |
| Not verifiable | Depends on infra or prod state that no repo holds | Other |

## Recording a change by hand

Use the `production-audit` skill's register script (or edit `data/findings.json` directly):

```bash
python3 -I <skill>/scripts/register.py set docs/PRODUCTION-AUDIT CQB-07 --status FIXED --evidence "PaymentClient.java:104" --note "Read timeout now goes to reconciliation, not resend"
python3 -I docs/PRODUCTION-AUDIT/build-viewer.py
```

When editing the JSON directly:
1. Set `status`.
2. If the status changed, set `since` to today.
3. Fill in `evidence` and `note`.
4. Append `{"date", "status", "note"}` to `history`.

Rebuild after any change, then republish `audit-viewer-shared.html` to the same link.
