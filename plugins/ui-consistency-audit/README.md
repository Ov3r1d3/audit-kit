# ui-consistency-audit

A read-only, multi-agent audit of a web frontend for visible UI bugs and style drift.

It maps the stack and theme mechanics first, including the CSS cascade facts that make some utility classes silently do nothing. Then four agents audit, in parallel:
- page structure;
- controls and forms;
- states, feedback and copy;
- visual tokens and theming, including dark mode.

Every high-severity claim is re-verified before it reaches the report. The result is one prioritized report: real bugs first, then sizes, inconsistent patterns, copy, dead code, and why some classes have no effect.

Ask, for example:
- "Audit the UI for inconsistencies."
- "Check the frontend for leftovers from before the redesign."
- "Why does dark mode look broken on some pages?"

Report only: it never edits files.

## Install

```
/plugin marketplace add Ov3r1d3/audit-kit
/plugin install ui-consistency-audit@audit-kit
```
