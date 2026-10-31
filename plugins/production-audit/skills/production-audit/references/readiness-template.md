# Launch-readiness page template

Path: `<root>/<project>/launch-readiness.md`. Rewrite it on every run as the **current state**:
- No "re-audit" framing, no "since last week" sections. Each finding's history lives in the register.
- The blocker table is generated from `data/blockers.json` at the marker.
- Cite finding and blocker IDs as plain text (`LB-07`, `MONEY-02`); the viewer turns them into links to their rows.

```markdown
# <Project label> launch readiness

**Scope:** `<repo>` (`<sha>`), `<repo>` (`<sha>`). Status as of **<YYYY-MM-DD>**. Static, read-only review: nothing was built, run or load-tested.

## Recommendation: **NO-GO**

**<N> launch blockers: <a> fixed, <b> accepted by decision, <c> partly fixed, <d> open.** <Two or three sentences: what moved, what did not, what is new.>

**Mapped to the client's fears:**
1. **<Fear 1>.** <Protected / partly / unprotected>:
   - <one line per concrete gap, citing IDs>
2. **<Fear 2>.** …
3. **<Fear 3>.** …

**What is sound:**
- <things checked and found correct, so readers know they were not skipped>

## Launch blockers

Each blocker's status and the date it last changed come from the register. Filter with the dropdown. Source findings link to their streams.

<!-- blockers:<project key> -->

**Conditional items** that are cleared by an operational decision or fixed:
- **<ID>:** <what, and the decision that clears it>

## Questions that gate go-live

| # | To | Question | Gates |
|---|---|---|---|
| Q-A | <vendor/client> | <question> | <blocker IDs> |

## Order of operations

(One Mermaid flowchart. Validate it with scripts/check_mermaid.mjs. No semicolons inside labels; quote labels that contain parentheses or slashes.)

**Estimate:** <developer-weeks + infra days → calendar weeks, and what it is counted from>.

**Do first:**
1. <first action>

## <Other project>

<How this project's verdict interacts with the other one: whether both must be GO, and what a partial launch needs.>

## Top post-launch follow-ups
1. <item>

## Limits

- <what was static only, what infra was not reachable, what was reviewed from untracked files>
```

Rules for the verdict:
- **NO-GO** while any blocker is OPEN, PARTIAL or REGRESSED. An ACCEPTED blocker counts as closed only if the page says why the decision is safe.
- **GO** needs every blocker closed, plus the release gate written in the order of operations (for example: E2E green, a forced DLQ message raises an alert, a restore drill done).
- Never call something fixed that the register does not show as FIXED.
