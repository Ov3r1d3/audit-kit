# Agent briefs

Fill in the `<…>` placeholders and give one brief per agent. A sub-agent knows only what its brief says, so each one must stand on its own.

The orchestrator writes a shared brief file once (to the scratchpad, never into the repo) and points every agent at it. That keeps each Agent call short.

## A. First-audit stream agent

```
You are Stream <letter> — <title> of a pre-production audit of <product> (<one-line description>).
Workspace: <absolute path>. Ground truth: <CLAUDE.md paths>. Treat them as true; if code contradicts them, that is a finding.

Scope: <dirs/files>. Exclude <docs/, scripts/, generated, protected paths>.
Check: <the stream's checks from references/streams.md, adapted to this stack>.
Known/accepted items: <list from CLAUDE.md "Known issues" etc.>. Cite these, do not re-raise them.

The client's fears drive severity:
1. Not sending / silently losing work.
2. Charging without consent, or twice.
3. Unauthorized access.
<adapt these to the product>

Write exactly one file: <root>/history/<date>-<project>-audit/<NN>-<slug>.md
Follow the "Stream report" format in <skill>/references/formats.md exactly. Use ID prefix <PREFIX>.
Every finding needs:
- a file:line;
- a concrete consequence ("a customer who cancels is still billed", not "race risk");
- a fix and an effort.

Read-only: no edits to application code, no builds, tests, migrations or network installs, no git operations beyond log/diff/show/blame. Never print secret values.

Before finishing, re-open every finding and confirm the file:line still says what you claim.
A stream with zero findings lists exactly what it checked.
Reply with: counts by severity, the launch-blocker IDs, and the top 3 risks.
```

## B. Re-check stream agent

```
Re-check <stream title> of the <product> production audit.
Workspace: <absolute path>. Audit folder: <root>.

Baselines → current HEAD (repos were just pulled):
<repo>: <baseline sha> → <head sha> (<N> commits). Run `git -C <repo> log <base>..HEAD` and `git diff <base>..HEAD`.
Notable new code in your area: <list from the diff stat>.

Findings to re-verify: every record in <root>/data/findings.json with "stream": "<key>".
For each one you get: its id, severity, location, description, fix, current status and evidence.
Line numbers drift: find the code by symbol.

Write exactly one file: <root>/history/<date>-recheck/<key>.md
Follow the "Re-check status file" format in <skill>/references/formats.md exactly:
- One row per finding, including ones already FIXED.
- Status is one of FIXED / PARTIAL / OPEN / REGRESSED / ACCEPTED / NOT-VERIFIABLE.
- Never mark FIXED from a commit message: read the code.
- Docs-only changes don't fix code defects.

Then review the new code in your area for new defects. Give them IDs <PREFIX>-R<next number>, with the same file:line, consequence and fix bar as the first audit.

Read-only. No builds or tests. Never print secret values.
Reply with the STATUS-COUNTS line, the new findings, and the top 3 still-open risks.
```

## C. Cross-repo delta (secondary project not changed, primary project changed)

If a sibling project was audited against an older checkout of another repo, re-check every finding whose evidence or consequence involves that other repo:
- contract fields
- shared enums and code mappings
- message type allow-lists
- expiry and idempotency handoffs

Findings that are purely internal to an unchanged repo are marked `OPEN` with the note "unchanged since audit". They still get a row.

## D. Orchestrator verification (both modes)

Before writing a verdict, re-open the code yourself for:
- every CRITICAL finding;
- every blocker whose status changed;
- every new HIGH or CRITICAL finding.

Mark each one you checked with **[V]** in the readiness page.

When two streams disagree about the same defect, decide it from the code and say which stream was right.
