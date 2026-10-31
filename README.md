# production-audit

A Claude Code skill for evidence-based **pre-production audits** that stay useful after launch day.

- **Full audit:** parallel review agents for code, security, database, performance, UX, accessibility, product gaps, docs, money paths, messaging and ops. Plus an architecture wiki, CLAUDE.md proposals and an explicit **Go / No-Go** verdict.
- **Living register:** every finding is one row with its current status (Open, Partial, Fixed, Regressed, Accepted, Not verifiable) and the date it last changed.
- **Re-audit:** pull the latest code, re-check every finding, mark what's fixed, add new findings, re-judge the verdict.
- **Viewer:** one self-contained HTML page with an overview per project, one filterable table per stream, expandable evidence and history, launch blockers, and reference docs. A redacted copy is produced for sharing.

## Install

In Claude Code:

```
/plugin marketplace add Ov3r1d3/claude-production-audit
/plugin install production-audit@production-audit
```

Or from a terminal:

```bash
claude plugin marketplace add Ov3r1d3/claude-production-audit
claude plugin install production-audit@production-audit
```

## Use

Just ask:
- "Run a full production audit of this repo before we launch."
- "Re-audit: what's fixed since the last audit?"
- "Add the payments-service repo to the audit."
- "Mark CQB-07 as fixed, it's in commit abc123."

The audit lives in `docs/PRODUCTION-AUDIT/`. Open `index.html` in a browser.

## Requirements

- Claude Code with sub-agents.
- Python 3.10+ for the register and viewer scripts (standard library only).
- Optional: Node 18+ to validate Mermaid diagrams (`skills/production-audit/scripts/check_mermaid.mjs`, setup in its header).

The audit is read-only: it never edits application code, CLAUDE.md, or anything outside the audit folder.

## License

MIT
