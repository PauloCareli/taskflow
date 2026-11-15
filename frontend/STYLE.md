# Frontend style guide

Dark theme only for v1. Tokens are defined once as CSS variables and mapped into Tailwind's theme; components use semantic names, never hex values.

## Color tokens
| Token | Hex | Use |
|---|---|---|
| canvas | `#0d1117` | page background |
| surface | `#161b22` | cards, header, dialogs |
| border | `#30363d` | dividers, input borders |
| fg | `#e6edf3` | main text |
| fg-muted | `#8b949e` | secondary text |
| accent | `#2f81f7` | primary buttons, focus ring |
| accent-fg | `#58a6ff` | links, active states |
| success | `#3fb950` | completed |
| attention | `#d29922` | due soon, blocked |
| danger | `#f85149` | overdue, destructive actions |

Contrast: body text and controls must meet WCAG AA against their background.

## Status mapping
| Status | Badge |
|---|---|
| todo | muted (border + fg-muted) |
| in_progress | accent |
| blocked | attention |
| completed | success |
| cancelled | muted, line-through title |
Overdue (due date passed and not completed/cancelled) is shown with `danger` plus an icon or text, not color alone.

## Typography
- System UI font stack for text, monospace stack for code/ids.
- Scale: 12 / 14 / 16 / 20 / 24 px; body 14-16px, line height 1.5; headings semibold.

## Spacing and shape
- 4px base unit; use Tailwind's spacing scale.
- Radius 6px for controls and cards, 999px for badges.
- Borders 1px `border`; avoid shadows except for dialogs.

## Breakpoints
Tailwind defaults: base (mobile first, 360px minimum), `md` 768px, `lg` 1024px. Tables collapse to stacked cards below `md`.

## Components
- **Button**: primary (accent), secondary (surface + border), danger. Visible 2px focus ring in `accent`. Disabled and loading states.
- **Input/Select**: surface background, border, accent focus ring, inline error text in `danger` with `aria-describedby`.
- **Dialog**: for destructive confirmations and forms; focus trapped, Esc closes.
- **Feedback**: inline messages for field errors, toasts for success/failure of mutations, skeletons for loading, a clear empty state with a call to action.
