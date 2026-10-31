# Stream catalog

Choose the streams in Phase 0:
- Drop any stream that does not apply, for example SEO for a non-public product, or accessibility and frontend streams for a backend-only service.
- Add the domain streams the charter identifies. The domain streams below carried the most weight on the audit this skill came from.

Each stream has:
- a **key** (used in `audit.json`, for the stream page and for re-check file names);
- an **ID prefix**, unique across the whole audit;
- an **agent type**;
- an **output** file.

Pick agent types that exist in the session; the names below are what the Claude Code ecosystem usually provides. Where no specialist exists, use `general-purpose` and paste the scope.

## Core streams

| NN | Key | Prefix | Agent | Scope and what to check |
|---|---|---|---|---|
| 10 | `be-code` | CQB | language reviewer (`java-reviewer`, `typescript-reviewer`, `python-reviewer`, `go-reviewer`…) | Backend source, excluding docs, scripts and generated code. Type and null-safety holes, async/concurrency correctness, swallowed errors (catch-log-continue), framework anti-patterns for the exact framework version, transaction boundaries around external I/O, time zones, dead code |
| 10b | `fe-code` | CQF | `typescript-reviewer` | Frontend source: the same checks, plus client-visible secrets and server/client boundaries |
| 11 | `security` | SEC-A | `security-reviewer` (skill `security-review`) | Auth flows, webhooks and callbacks, cron and internal endpoints, secret and env exposure, rate limiting, injection (SQL, search, filter), open redirects, timing-safe comparisons, authz bypass (tenant isolation, role checks, a "null scope = admin" fallback), deserialisation, dependency age/CVEs (no network installs). Map findings to OWASP Top 10 |
| 12 | `database` | DB | `database-reviewer` | All migrations (frozen vs editable), constraints, indexes, stored procedures, the transactional integrity of the money/state-critical write paths, N+1 and unbounded queries, pool sizing vs consumer concurrency, seeded data (default accounts), backups/PITR evidence |
| 13 | `performance` | PERF | `performance-optimizer` (audit only, no edits) | Hot query shapes, outbound HTTP timeouts and bulkheads, queue head-of-line blocking, cache key collisions, bundle and cold-start weight, rendering boundaries, re-render storms, the heaviest data pipeline |
| 14 | `ux` | UX | `code-reviewer` (frontend focus; skills `frontend-patterns`, `frontend-design`) | Every user-facing surface: design-token discipline, breakpoints 320/768/1024/1440, reduced motion, loading/error/empty states on every async surface, destructive actions without confirmation, silent failures (exports, toasts) |
| 15 | `a11y` | A11Y | `a11y-architect` | WCAG 2.2 AA on the 3–5 primary flows: keyboard, contrast in every shipped theme (show the arithmetic), dialog focus management, form labels, ARIA on navigation, `lang` on foreign-language content, reflow at 320px. Add a `WCAG` column |
| 16 | `seo` | SEO | `seo-specialist` (skill `seo`) | Public pages only: title/meta/OG/canonical, JSON-LD, sitemap, robots, slug stability, hreflang. For a private admin product: only a `noindex` guard |
| 17 | `product` | PROD | `general-purpose` | Walk every flow end to end (onboarding → core loop → payment → notifications → account → offboarding). Missing functionality, edge cases, error recovery, refund/cancel visibility, locale and currency, support contact, legal pages and consent. Re-check the open client questions. Score each gap blocker or post-launch |
| 18 | `docs` | DOC | `Explore` (very thorough) or `general-purpose` | Every file under `docs/` except protected paths (list them). One row per file: `File \| Tag (KEEP/UPDATE/ARCHIVE/DELETE) \| Reason \| Hints worth mining`. Claims checked against code. **Classification only, no deletions** |

## Domain streams (add when the charter finds them)

| NN | Key | Prefix | Agent | When and what |
|---|---|---|---|---|
| 19a | `money` | MONEY | `general-purpose` | Anything that charges, bills or moves money. Trace each billable path end to end: ambiguous submits (timeout after acceptance → resend → double charge), idempotency keys, caps and quotas (reserve vs count), per-segment/per-unit billing, refunds, revenue computation (inner joins that drop unpriced traffic), month/period bucketing time zone. Add an E2E coverage map: an untested CRITICAL path is itself a finding (prefix `MONEY-T`) |
| 19b | `messaging` | MSG | `silent-failure-hunter` | Queues, events, webhooks. Table: queue \| producer/listener file:line \| ack and retry \| on exhaustion \| idempotent on redelivery? \| alerting?. Check DLQs without consumers, publisher confirms, graceful shutdown, catch-log-continue, retries that repeat non-idempotent writes |
| 19c | `ops` | OPS | `general-purpose` | Prod config fail-fast (does a missing env var stop startup, or boot "healthy"?), deploy scripts vs unit files, rollback safety of migrations, graceful shutdown and LB drain, backups and restore drill, metrics and alerts, log levels and persistence, runbooks. Appendix A: env-var inventory (names only, never values). Appendix B: existing metrics |
| — | `contract` | SCON | `general-purpose` | Two services exchanging messages: field-by-field diff of every message both ways (names, types, type headers, enum names, time zones, compression), and a check that the contract doc matches both codebases |
| — | `tests` | STEST | `pr-test-analyzer` | Map every CRITICAL/HIGH behaviour to a unit or E2E test. Flag vacuous assertions (a "not sent" check that always passes) |
| — | `protocol` | SMONEY | `general-purpose` | Wire protocols (payment gateways, carrier or messaging protocols, partner APIs): resend semantics, segmentation and encoding, correlation ids, receipt parsing, validity/expiry |
| — | `resilience` | SPERF | `performance-optimizer` | Long-lived connections: reconnect and backoff, keepalive, session limits vs failover, cluster split-brain, unbounded in-memory maps |

Other domain streams to consider: multi-tenancy isolation, mobile apps, ML pipelines, data retention and GDPR.

## A second project (sibling service, connector, worker)

Audit it as its own **project**, with its own blocker prefix (`CB`, …) and its own streams. The keys need a project prefix (`c-code`, `c-security`, …) and so do the ID prefixes (`SCQ`, `SSEC`, …), so they never collide with the first project's.

Keep architecture light: a single `reference/<project>-architecture-brief.md`, at most about 150 lines, with one flowchart and one sequence diagram, instead of a wiki. Add the `contract` stream against the project it talks to.
