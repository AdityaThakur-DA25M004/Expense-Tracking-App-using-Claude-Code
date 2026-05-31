---
name: spendly-ui
description: >
  Frontend UI generator for the Spendly expense tracker app (Flask + Jinja2 + CSS/JS).
  Generates modern, production-ready HTML/CSS/JS pages and components that match Spendly's
  clean fintech design system — card-based layouts, 8px grid, soft shadows, Lucide icons.
  Use this skill whenever the user says things like "design the ___ page", "create UI for ___",
  "build component for ___", "redesign / improve ___", or any request involving Spendly UI.
  Even vague requests like "make the dashboard nicer" or "add a spending chart" should trigger
  this skill. Always use it for any Spendly-related UI work, even if the user doesn't say "Spendly"
  explicitly — context clues like "expense tracker", "transactions page", "budget widget" are enough.
---

# Spendly UI Skill

Generates clean, production-ready UI for the **Spendly** expense tracking application.
Spendly is a Flask + Jinja2 app with HTML templates, a CSS design system, and minimal JS.

---

## Stack & Context

- **Backend**: Python / Flask
- **Templates**: Jinja2 HTML (in `/templates/`)
- **Styles**: Custom CSS (in `/static/css/`)
- **Icons**: Lucide Icons (via CDN) or Heroicons
- **JS**: Vanilla JS or Chart.js for data viz — no React/Vue
- **Existing repo**: https://github.com/campusx-official/spendly

---

## Design System

### Layout
- Card-based layout with `border-radius: 12px` and soft `box-shadow`
- 8px spacing grid: use multiples of 8px for all margins, padding, gaps
- Max content width: `1200px`, centered
- Responsive: mobile-first, two-column grid on desktop

### Colors
```css
--color-bg:          #F7F8FA;   /* page background */
--color-surface:     #FFFFFF;   /* card/panel background */
--color-border:      #E8ECF0;   /* subtle borders */
--color-primary:     #6C63FF;   /* primary action / brand */
--color-primary-light: #EEF0FF; /* tinted bg for primary elements */
--color-success:     #22C55E;   /* income / positive */
--color-danger:      #EF4444;   /* expense / negative */
--color-warning:     #F59E0B;   /* budget alerts */
--color-text:        #1A1D23;   /* primary text */
--color-text-muted:  #6B7280;   /* secondary text */
--shadow-sm:  0 1px 3px rgba(0,0,0,0.08);
--shadow-md:  0 4px 12px rgba(0,0,0,0.10);
--shadow-lg:  0 8px 24px rgba(0,0,0,0.12);
```

### Typography
- **Font**: `'DM Sans', sans-serif` (load from Google Fonts) — clean, modern, slightly geometric
- Page title: `24px`, `font-weight: 700`
- Section heading: `18px`, `font-weight: 600`
- Body: `14px`, `font-weight: 400`
- Muted label: `12px`, `color: var(--color-text-muted)`

### Components
```
Card:          background: white; border-radius: 12px; padding: 24px; box-shadow: var(--shadow-sm);
Stat card:     icon (32px, tinted bg) + label + big number + trend badge
Badge:         border-radius: 999px; padding: 2px 10px; font-size: 12px; font-weight: 500
Button primary: background: var(--color-primary); color: white; border-radius: 8px; padding: 10px 20px
Input:         border: 1.5px solid var(--color-border); border-radius: 8px; padding: 10px 14px
Table:         thead with muted bg, tbody rows with hover state, zebra optional
```

### Icons
Use **Lucide** via CDN:
```html
<script src="https://unpkg.com/lucide@latest/dist/umd/lucide.min.js"></script>
<!-- Usage: -->
<i data-lucide="wallet" class="icon"></i>
<script>lucide.createIcons();</script>
```
Common icons for Spendly:
- `wallet` — overall balance
- `trending-up` / `trending-down` — income / expense
- `credit-card` — transactions
- `pie-chart` — analytics
- `target` — budget
- `plus` — add expense
- `filter` — filter controls
- `calendar` — date range

---

## What to Output

For every UI request, produce **two sections**:

### 1. UI Brief (short — 5–10 lines)
- Layout overview (what sections, what grid)
- Key UX decisions
- Any data assumptions made

### 2. Code
Full, self-contained HTML file (or Jinja2 template if backend data is needed).

**Code standards:**
- Clean CSS — use variables, no magic numbers
- Modular: one `<style>` block, one `<script>` block at bottom
- Semantic HTML: `<header>`, `<main>`, `<section>`, `<nav>`
- Minimal boilerplate — no unnecessary wrapper divs
- All dummy data clearly marked with a `<!-- REPLACE: ... -->` comment
- If Jinja2 template variables are needed, use `{{ variable_name }}` with a comment showing expected type

---

## Pages in Spendly

Reference these when building or extending:

| Page | Path | Purpose |
|---|---|---|
| Dashboard | `/` | Summary: total balance, recent txns, spending chart |
| Transactions | `/transactions` | Full list with filter/search |
| Add Expense | `/add` | Form to log a new expense |
| Analytics | `/analytics` | Charts: by category, trend over time |
| Budget | `/budget` | Set and track category budgets |

---

## Design Rules

✅ Do:
- Rounded corners everywhere (8–16px)
- Soft, layered shadows
- Consistent 8px spacing
- Tinted icon containers (e.g., `background: var(--color-primary-light)`)
- Subtle hover states (`background: #F7F8FA` on rows, `translateY(-1px)` on cards)
- Color-code amounts: green for income, red for expense

❌ Avoid:
- Generic/dated UI (no Bootstrap defaults, no flat grey tables)
- Unstructured code dumps
- Hardcoded colors or pixel values
- Random icon styles mixed together
- Overloaded pages with too much information density

---

## Consistency Rule

If the user shares screenshots or existing code, **match that design first** before introducing anything new. If the existing design is unclear, ask: _"Can you share a screenshot of the current UI so I can match it?"_

---

## Example Output Pattern

**User:** "Design the dashboard page"

**You output:**

> **UI Brief:** Two-column layout — left column has summary stat cards (balance, income, expense this month), right column has a donut chart. Below: recent transactions table (last 5). Top nav has app name + add-expense CTA button.

Then: complete `dashboard.html` following the design system above.

---

## Quick Reference

- Load DM Sans: `<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">`
- Load Lucide: `<script src="https://unpkg.com/lucide@latest/dist/umd/lucide.min.js"></script>`
- Load Chart.js (if needed): `<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>`
- Always call `lucide.createIcons()` at the end of your script block