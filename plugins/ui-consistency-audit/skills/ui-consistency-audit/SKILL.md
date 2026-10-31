---
name: ui-consistency-audit
description: Read-only, multi-agent UI consistency audit of a web frontend. Finds visible bugs and style drift (sizes, theming, dark mode, controls, states, copy, dead code), verifies the claims, and delivers one prioritized report. Use when asked to "check for inconsistencies", "audit the UI", or "find leftovers from before the redesign".
---

# UI consistency audit

Audit a frontend for inconsistencies and visible UI bugs. **Report only: change no files.**

## Inputs (ask only if they can't be inferred)

- Frontend root (e.g. `apps/web/src`). Default: the repo's main frontend source folder.
- Known reference pages or patterns the user considers "correct" (optional). If none, discover them in Step 1.
- Where the report goes: a shareable doc/page if a docs or artifact tool is available, otherwise a Markdown file `UI-AUDIT.md` at the repo root (ask before creating a top-level file).

## Step 1: Map the system (you, before spawning agents)

Spend a few minutes so every agent works from the same facts:

1. Stack: framework, styling (Tailwind version, CSS modules, CSS-in-JS), component library (shadcn/Radix, MUI, …), icon library, i18n.
2. Theme mechanics: where tokens live, dark-mode switch (class vs media), any alternate themes (e.g. a glass mode). **Check CSS cascade order and specificity**: unlayered theme CSS with selectors like `.theme h1` or `[data-slot=button][data-size=sm]` silently beats single utility classes. Then height, font-size and radius utilities in the code may do nothing. Record which control sizes the theme really enforces.
3. Token pitfalls: e.g. a border token that is only correct when combined with an opacity variable. Raw uses then render wrong (solid white lines in dark mode).
4. Canonical patterns: pick 2–3 recently built, well-regarded pages and write down their page header, list/table, row actions, forms, dialogs, segmented controls/tabs, loading/empty/error states. Tag "reference: <file>" for each.
5. Note deliberate exceptions the code documents (e.g. wizards using 44px touch targets).

Write this as a short **Context brief** and paste it into every agent prompt.

## Step 2: Fan out read-only agents (in parallel, one message)

Spawn 4 Explore/read-only agents. Each gets the Context brief and these rules:

> READ-ONLY. Do not edit anything. Skip tests and stories. For each finding give `file:line`, what it does, the canonical pattern, and severity: **high** = a visible bug or something a user would clearly notice; **medium**; **low**. Verify every claim by reading the code: no speculation. List every instance, not examples. Flag components/CSS imported nowhere as **[dead]**. Group by category; include counts.

**Agent A: Page structure.**
- Page headers (h1 size/weight, subtitle, action placement) and detail pages.
- Lists/tables built by hand instead of the shared table component, and inconsistent table config (search/filter slots, error prop, pagination, empty copy).
- Row actions not using the shared component.
- Section heading levels and sizes for the same role.
- Page container spacing and max-widths.
- Back links vs breadcrumbs.
- Public/unauthenticated screens vs their shared shell.

**Agent B: Controls and forms.**
- Hardcoded heights/paddings vs the theme sizes (remember which ones the theme overrides and which still win, such as `min-h-*`).
- Controls the theme doesn't reach (native elements, primitives that skip the size attributes).
- Mixed button variants for the same role (Cancel, destructive).
- Segmented controls/tabs not using the shared component.
- Native `select` / date / time inputs.
- Form field structure (label placement, label styles, error and required markers, broken label→control links).
- Switch-row layouts, and redundant "override + enabled" double switches.
- Dialog footers and confirmation mechanisms (`window.confirm`).
- Icon-only buttons without tooltip/label, and icon sizing APIs.
- **Scrollable lists in portaled popovers inside modal dialogs/sheets.** They can't be scrolled with the mouse wheel.

**Agent C: States, feedback, copy.**
- Loading (skeleton vs text vs spinner vs nothing, `…` vs `...`, `role="status"`).
- Empty states.
- Error states: **queries whose error is ignored so a failure renders as empty or "all clear"**, error copy patterns, raw `error.message`, `role="alert"`, and JSX whitespace that glues a label to an interpolated value.
- Toasts: duplicate hook + component toasts, per-item toast spam, copy style.
- Title Case vs sentence case (table of variants with counts).
- Badges for the same concept, raw lowercase enum values shown via CSS `capitalize`.
- Date/time formatters (list each one), relative-time styles, number/unit formatting.
- Confirmation copy.

**Agent D: Visual tokens and theming.**
- Hardcoded colors vs semantic tokens.
- Raw token uses that break dark mode (including inline chart props).
- `bg-white` / `text-black` without dark variants.
- Status colors re-declared in many places, or conflicting.
- Low-contrast status text.
- Border-radius scale drift and hidden radius overrides.
- Parallel card-surface systems and padding drift.
- Arbitrary font sizes, px font sizes in CSS, missing `tabular-nums` on numbers.
- Arbitrary spacing and inline `style` for static layout.
- Alternate-theme gaps, e.g. substring attribute selectors like `[class*='bg-muted/']` that also match `hover:` classes.
- Icon library and sizing.
- Duplicate CSS definitions of one concept.

Tell the user in one line what each agent covers, then wait. Don't do their searches yourself.

## Step 3: Verify before reporting

Agents overstate. Before writing anything up:

- Re-check every **high** finding yourself with a quick grep or read (e.g. the error flag is really never read, the raw token is really unlayered, the popover really portals).
- Resolve contradictions between agents (one says a CSS class is used, another says dead → grep it).
- Downgrade findings that live only in dead code.
- Mark anything you could not verify as "not verified" instead of asserting it.

## Step 4: Deliver one report

Structure, most important first:

1. **Lead sentence**: the count of real bugs vs smaller inconsistencies, and the one-line cause (e.g. "pre-redesign code never moved onto the new patterns").
2. **Fix first**: a tracker table: `# | Bug | Where (file:line) | Severity | Status`. Only true bugs: misleading states, dark-mode breakage, broken interactions, duplicate toasts, glued text, mismatched control heights, wrong destructive styling. Name the 1–2 fixes that clear the most findings at once.
3. **Sizes and spacing**: table: problem | renders at | where.
4. **Inconsistent patterns**: table: area | what varies | where | the majority pattern to converge on.
5. **Copy**: table: issue | examples | where | majority.
6. **Dead code**: bullet list, safe to delete.
7. **Why some classes do nothing**: the theme-override facts from Step 1, so fixers don't add more dead classes.

If a docs tool is available, publish there with Severity and Status as dropdown columns. Otherwise write Markdown. In chat, give a short summary plus the link. Don't paste the whole report twice.

## Rules

- Never edit source, commit, or "quickly fix" anything during the audit. Offer fixes afterwards.
- Another agent or person may be working in the repo: read-only also means no formatters, no `git stash`, no builds that write to tracked files.
- Prefer exact `file:line` and concrete strings over adjectives.
- Keep severity honest: style drift is medium or low. Reserve high for what users will see or be misled by.
