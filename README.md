# audit-kit

Evidence-based audit skills for [Claude Code](https://claude.com/claude-code).

| Plugin | What it does |
|---|---|
| [`production-audit`](plugins/production-audit) | Pre-production audit and re-audit. Parallel review agents, a living findings register with dated statuses, a Go/No-Go verdict, and a filterable HTML viewer |
| [`ui-consistency-audit`](plugins/ui-consistency-audit) | Read-only multi-agent audit of a web frontend for visible UI bugs and style drift, with every high-severity claim verified |

## Install

In Claude Code:

```
/plugin marketplace add Ov3r1d3/audit-kit
/plugin install production-audit@audit-kit
/plugin install ui-consistency-audit@audit-kit
```

From a terminal, use `claude plugin marketplace add …` and `claude plugin install …`.

To update later: `/plugin marketplace update audit-kit`, then `/plugin update <plugin>@audit-kit`.

## License

MIT
