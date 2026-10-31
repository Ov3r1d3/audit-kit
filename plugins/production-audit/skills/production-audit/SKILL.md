---
name: production-audit
description: Run an evidence-based pre-production (staging → production) audit of a codebase with parallel review agents, and keep it as a living findings register with an interactive viewer. Covers code quality, security, database, performance, UX, accessibility, product gaps, docs, money/billing paths, messaging reliability and ops readiness, plus an architecture wiki, CLAUDE.md proposals and a Go/No-Go launch-readiness verdict. Also re-audits an existing audit after code changes and marks every finding Fixed / Partial / Open with dates, adds a new project or repo to an existing audit, or records a single fix. Use this whenever the user asks for a production audit, launch readiness review, go-live check, pre-launch review, security/code sweep before release, Go/No-Go, "re-audit", "check what is fixed", "update the audit", or wants an audit added for another repo or service — even if they don't say "skill".
---

# Production audit

This skill produces an audit folder (default `docs/PRODUCTION-AUDIT/`) that stays useful after the first run:

- **One register.** `data/findings.json` and `data/blockers.json` hold **one row per finding**, with its current status and the date it last changed. A re-audit updates rows; it never adds parallel "re-audit" reports for readers to reconcile.
- **One viewer.** `build-viewer.py` turns the register into a single HTML page:
  - an overview per project;
  - one filterable table per stream (status dropdown, severity, search, blockers only);
  - expandable rows with evidence and history;
  - launch readiness per project;
  - reference docs.
- **Raw reports** of every run go to `history/`, for traceability. The viewer shows only their scope and method notes.

Read `references/formats.md` before the first agent is dispatched: the parser depends on exact table headings.

## Pick the mode

| The user wants… | Mode |
|---|---|
| A first audit of a product | **A. Full audit** |
| Another repo or service added to an existing audit | **B. Add a project** (Mode A, scoped, light architecture) |
| To know what got fixed since the last audit | **C. Re-audit** |
| To mark one finding fixed, accepted, … | **D. Record a change** |
| The viewer shared | **E. Publish** |

An existing `docs/PRODUCTION-AUDIT/data/audit.json` means an audit exists: use B, C or D, never start over.

## Ground rules (every mode)

- **Read-only.** Never modify application code, CLAUDE.md files or anything outside the audit folder. No builds, tests, migrations, network installs into the repo, or connections to brokers or databases. Git is limited to `log`, `diff`, `show`, `blame`, plus `pull --ff-only` in Mode C when the user asked for it. If a repo has local changes, say so and do not pull it.
- **Every finding has four things:**
  - a `file:line`;
  - a **concrete consequence** ("a subscriber is charged twice", not "race risk");
  - a suggested fix;
  - an effort (S/M/L).

  "Could be improved" is rejected.
- **No deletions.** The docs stream classifies files only.
- **Secrets.** Never print secret values. When a report quotes a literal default password or key, add it to `redact` in `data/audit.json`, so the shared copy never carries it.
- **Dispatch at most 3 Agent calls per message.** Larger fan-outs have failed silently. Launch them as background agents. When one finishes, launch the next stream, so three always run.
- **Verify before claiming.** Apply `superpowers:verification-before-completion` if available. The orchestrator re-opens the code for every CRITICAL finding, every changed blocker and every new HIGH (`references/agent-briefs.md` §D). A stream with zero findings states what it checked.
- **Mermaid** must parse with mermaid@11.4.1, the version the viewer loads. Validate with `scripts/check_mermaid.mjs`; its header has the one-time setup.
- **Ground truth is CLAUDE.md.** Use it, the README and the design docs. A contradiction between docs and code is a finding. If there is no CLAUDE.md, that is finding #0; derive the stack from lockfiles and config.

Scripts live in `<skill>/scripts/` and run with `python3 -I`. `register.py` is the only thing that edits the JSON files in normal use.

---

## A. Full audit

**Phase 0: charter.** Apply `superpowers:brainstorming` if available. Don't stall on questions: answer them with the most defensible default and record the answers in the charter.

1. **Scaffold the folder:**
   ```bash
   python3 -I <skill>/scripts/register.py init <root> --product "<Name>" --project "platform:Platform:<subtitle>:LB"
   ```
2. **Choose streams** from `references/streams.md`:
   - drop what doesn't apply;
   - add domain streams (money, messaging, ops, contract…);
   - fix each stream's key, ID prefix, agent and report path `history/<date>-<project>-audit/<NN>-<slug>.md`.
3. **Register the streams** in `data/audit.json` under `streams`. Also record the audited HEAD of each repo in an `audits` entry (`commits`), so a later re-audit has a baseline. Add the reference pages to `reference`.
4. **Write the charter** to `reference/<project>-charter.md`. It holds:
   - the stream table: key, prefix, agent, output, parallel or sequential;
   - the severity rubric (below);
   - protected paths;
   - the client's fears;
   - the known issues that are cited rather than re-raised.

Severity rubric:
- **CRITICAL:** data loss, money lost or misbilled at scale, or auth bypass.
- **HIGH:** a user-visible failure or a security weakness with a realistic path.
- **MEDIUM:** degraded behaviour, or a gap with a workaround.
- **LOW:** hygiene.

A finding is a launch blocker if it is CRITICAL, or HIGH and it touches the client's fears.

**Phase 1: streams.**
1. Write the shared brief (`references/agent-briefs.md` §A) to the scratchpad.
2. Dispatch the streams, three at a time (apply `superpowers:dispatching-parallel-agents` if available).
3. Each agent writes exactly its own report, in the format of `references/formats.md` §2.

**Phase 2: architecture.** Primary project: the wiki in `references/wiki.md`. Secondary projects: a brief.

**Phase 3: CLAUDE.md proposals.**
- Write to `reference/<project>-claude-md-proposals.md`.
- Each proposal has a category (gotcha, open risk, file map, convention, env var, other), the target file and section, the exact proposed text, and file:line evidence.
- **Propose only. Never edit a CLAUDE.md.**

**Phase 4: verdict.**
1. Write `history/<date>-<project>-audit/99-blockers.md`. It de-duplicates the `Launch Blocker = Y` rows into root-cause blockers (`formats.md` §3).
2. Ingest the reports and blockers:
   ```bash
   python3 -I <skill>/scripts/register.py ingest <root> --project platform --date <date> --reports history/<date>-platform-audit
   python3 -I <skill>/scripts/register.py status <root>
   ```
3. Verify per §D of the briefs.
4. Write `<project>/launch-readiness.md` from `references/readiness-template.md`. Include:
   - an explicit **GO / NO-GO**;
   - the client's fears;
   - questions that gate go-live;
   - the order of operations (Mermaid);
   - an estimate;
   - limits.
5. Run `register.py validate`, the Mermaid check and `python3 -I <root>/build-viewer.py`. Fix anything reported.
6. Report to the user: the verdict, counts, top blockers, the questions to send today, and where the viewer is. Offer Mode E.

## B. Add a project

Same as A for one more project (connector, worker, sibling repo):
1. **Add the project:** append it to `projects` in `data/audit.json`, with its own `blockerPrefix` (`CB`…).
2. **Prefix its streams:** stream keys such as `c-code`, and ID prefixes such as `SCQ`, so nothing collides with the first project.
3. **Drop the streams that don't apply.** A service with no UI or database needs no UX, accessibility, SEO or database stream.
4. **Add a `contract` stream** against the project it talks to.
5. **Architecture is a brief,** not a wiki.
6. **Ingest with `--project <key>`.** The overview then shows both projects side by side.

## C. Re-audit (what is fixed?)

1. **Baselines.**
   - Read `data/audit.json` → `audits[].commits` for each repo's last audited HEAD.
   - If the user asked, pull every repo with `git pull --ff-only`, reporting dirty trees instead of forcing.
   - Record `base..HEAD` for each repo, with commit counts and a diff stat.
   - If a repo was audited against an *older checkout of a sibling repo*, plan a cross-repo delta (briefs §C).
2. **Re-check streams.**
   - Run one agent per stream, three at a time, with the brief in `references/agent-briefs.md` §B.
   - Each writes `history/<date>-recheck/<stream-key>.md` in the format of `formats.md` §4: a row for **every** finding of that stream, plus new findings (`<PREFIX>-R<nn>`).
   - Agents read their findings from `data/findings.json`, not from old reports.
3. **Verify and adjudicate.**
   - Re-open the code for each status change on a CRITICAL or HIGH finding or a blocker, and for every new HIGH.
   - Where streams disagree, decide from the code; a later stream may prove an earlier "FIXED" wrong.
   - Write `history/<date>-recheck/blockers.md` (`formats.md` §5). It covers every existing blocker, plus new blockers raised by new findings.
4. **Apply.** `register.py recheck <root> --date <date> --checks history/<date>-recheck`, then `status`. Add an `audits` entry with the new commits.
5. **Rewrite each `<project>/launch-readiness.md` as current state.**
   - Re-judge the verdict, the estimate and the order of operations.
   - Questions never sent are themselves news. Say so.
6. **Validate, check Mermaid, build.** Report to the user:
   - findings fixed, partial and open by severity;
   - blockers closed and still open;
   - the new blockers;
   - the verdict and what changed it.

   If a viewer was published before, republish it to the same link (Mode E).

## D. Record a change

For a single status change the user reports ("CQB-07 is fixed in commit abc"):
1. Read the code to confirm the change.
2. Record it:
   ```bash
   python3 -I <skill>/scripts/register.py set <root> CQB-07 --status FIXED --evidence "`File.java:104` (abc123)" --note "<why it can no longer happen>"
   python3 -I <root>/build-viewer.py
   ```
3. If the finding feeds a blocker, update that blocker too, and the readiness prose if the verdict moves.

## E. Publish

`audit-viewer-shared.html` is the redacted copy, with the document skeleton stripped for artifact hosts.

- **With an Artifact tool:** publish that file. On later runs, republish to the **same URL**.
- **If the publish is refused** because a newer version exists, compare its embedded data with the local sources before merging. A differing document is usually an earlier build artifact or a superseded layout; real content edits must be carried into the register or the markdown, never lost.
- **Without an Artifact tool:** `index.html` opens directly in a browser. To view it locally, serve the folder with any static server.

Before publishing:
- grep the shared file for every `redact` literal;
- confirm the build printed no "STILL CONTAINS" warning.

## Lessons this skill encodes

- **Re-check against the right code.** An audit of repo B that read repo A before A was pulled goes stale the moment A moves. Record commits per run and re-check cross-repo findings.
- **"Docs say X" is not evidence.** One audit found the docs claiming that a missing setting stops startup. The settings were bound without validation, so the node actually booted healthy and sent nothing. Confirm behaviour in code and library semantics.
- **Vacuous tests hide regressions.** A "not sent" assertion that cannot fail proves nothing. The tests stream checks the oracle before trusting coverage.
- **Rollback safety is part of every migration.** A new enum value written by a migration can break the previous release's nodes during a rolling deploy.
- **Readers want one current table, not a stack of dated reports.** Keep history in the register and write the narrative as current state.
