# production-audit

Evidence-based pre-production audits that stay useful after launch day.

- **Full audit:** parallel review agents for code, security, database, performance, UX, accessibility, product gaps, docs, money paths, messaging and ops. Plus an architecture wiki, CLAUDE.md proposals and an explicit **Go / No-Go** verdict.
- **Living register:** every finding is one row with its current status (Open, Partial, Fixed, Regressed, Accepted, Not verifiable) and the date it last changed.
- **Re-audit:** re-checks every finding against the latest code, marks what's fixed, adds new findings, re-judges the verdict.
- **Viewer:** one self-contained HTML page with an overview per project, one filterable table per stream, expandable evidence and history, and launch blockers. A redacted copy is produced for sharing.

Ask, for example:
- "Run a full production audit of this repo before we launch."
- "Re-audit: what's fixed since the last audit?"
- "Add the payments-service repo to the audit."
- "Mark CQB-07 as fixed, it's in commit abc123."

The audit lives in `docs/PRODUCTION-AUDIT/`; open `index.html` in a browser. Read-only: it never edits application code or CLAUDE.md.

**Requirements:** Claude Code with sub-agents, and Python 3.10+ (standard library only). Optional: Node 18+ to validate Mermaid diagrams.

## Install

```
/plugin marketplace add Ov3r1d3/audit-kit
/plugin install production-audit@audit-kit
```
