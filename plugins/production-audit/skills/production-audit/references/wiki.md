# Architecture wiki (Phase 2, primary project)

**Agent:** `architect` (or `general-purpose`), foreground, after Phase 1, so every subsystem named in a finding gets a page.
**Output:** `<root>/reference/architecture/`. Set `"wikiRoot": "reference/architecture/00-README.md"` in `data/audit.json` and add `[wikiRoot, "Architecture wiki"]` to `reference`.

Keep the numbering and adapt the file list to the product's real subsystems. Drop pages that don't apply, such as payments for a product with no payments.

| File | Content |
|---|---|
| `00-README.md` | Table of contents and how to read the wiki |
| `01-overview.md` | One page: what the product is, who uses it, the business model |
| `02-tech-stack.md` | Layered stack diagram, version matrix |
| `03-repo-structure.md` | Annotated tree of the top-level folders |
| `04-data-model.md` | ER diagram of all tables or collections |
| `05-request-lifecycle.md` | Sequence diagrams: page render, API request, background invocation, auth refresh |
| `06-core-flow.md` | Sequence and state diagrams for the money path or core domain lifecycle, including failure and recovery paths |
| `07-integrations.md` | Every third-party API: purpose, auth, cadence, webhook map, failure behaviour |
| `08-background-jobs.md` | Every cron or queue task: schedule, owner file, trigger source, idempotency |
| `09-auth-and-authz.md` | Auth flows, permission model, admin gates |
| `10-payments.md` | Payment flow, webhook contract, state machine, reconciliation |
| `11-deployment.md` | Topology, env-var ownership, rollback procedure |
| `12-observability.md` | Logs and metrics: what to watch and where to find it |
| `13-runbook.md` | On-call quickstart for the top 5 incident types |
| `14-glossary.md` | Domain terms |

Rules:
- **Every diagram is Mermaid. No ASCII art.** The viewer loads mermaid@11.4.1, so validate with `scripts/check_mermaid.mjs`. Common breakages:
  - semicolons inside sequence-diagram messages;
  - unquoted labels containing `(`, `)`, `/` or `:`;
  - `end` used as a node id.
- **Cite findings by ID** (for example "see SEC-A-02"), not by file link. IDs become live links to their rows, and file links break when reports move.
- **Pages describe the system, not its defects.** Mention a finding where it changes how something works, and leave the rest to the stream tables.

## Secondary projects: architecture brief

**Output:** `reference/<project>-architecture-brief.md`, at most about 150 lines:
- one paragraph on what the project is and where it sits;
- one flowchart of the components and transports;
- one sequence diagram of the most important path, with its failure branches;
- a table of the queues, connections and env vars that matter on day one.
