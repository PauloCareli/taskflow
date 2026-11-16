# 21 - Task list UI improvements

Issue: #21 · Depends on: 12-frontend-app · Layers: frontend

## Goal
Make the task list easier to scan and act on: a compact card per task with the description under the due date, a status tag that doubles as the status control, an overdue tag, row actions on the right (Complete visible, the rest under a kebab menu), a read-only task view in a modal, filters grouped in a card with a clear button, and the signed-in user's name in the header.

This refines the screens delivered in `12-frontend-app.md`. Where they differ, this spec wins: the status `select` described in 12/AC-07 becomes the status tag with a menu (AC-05), and the Edit and Delete buttons move into the kebab menu (AC-03).

## Out of scope
- Editing from the view modal (editing stays in the edit dialog).
- Profile editing, light theme, sorting controls, new filters.
- Backend changes. The user's name comes from existing endpoints.
- A table layout. The list stays a list of cards, so there are no columns to place the status in.

## Acceptance criteria

### Task card
- AC-01: Given a task with a description, when the list renders, then the description is shown below the due date and assignee line, limited to a single line; when it does not fit, it is cut with an ellipsis; and when the user hovers or focuses it, the full description is shown in a tooltip. Given a task with no description, then no description line is shown. The full text is available to assistive technology without hovering.
- AC-02: Given a task, then its status is shown as a tag below the description line, and given the task is overdue (due date passed and not completed or cancelled), then an overdue tag with text and an icon is shown next to the status tag, not by colour alone.
- AC-03: Given a task, when the list renders, then the actions are on the right of the card: Complete as a visible button (when the user may change the status), and a kebab button that opens a menu with View, Edit and Delete; Edit and Delete appear only for the creator, View for everyone who can see the task (the title opens the same view, AC-06). The menu is keyboard operable (opens with Enter or Space, arrow keys move, Escape closes and returns focus to the kebab), is named, and closes after an action or when focus or a click leaves it.
- AC-04: Given the menu, when the user chooses Edit or Delete, then the edit dialog or the delete confirmation from 12/AC-06 and 12/AC-08 opens exactly as before.

### Status control
- AC-05: Given a task whose status the user may change (creator or assignee, not completed or cancelled), then the status tag shows a caret that tells it is a dropdown; when the user activates it, then a menu of the other statuses (excluding completed, which is the Complete button) opens, and choosing one updates the task as in 12/AC-07, including the error messages and the list refresh. Given the user may not change the status or the task is completed or cancelled, then the tag is static and has no caret.

### Task view
- AC-06: Given a task, when the user chooses View or clicks the task title, then a modal opens showing title, full description, status, overdue tag when it applies, due date, creator, assignee, and created and updated dates; it has no editable fields; it is closed with an X button (named "Close"), with Escape, or by clicking outside, and focus returns to the kebab.
- AC-07: Given the view modal and a user who may change the status, then the modal has the same status control and Complete button as the card, and a change made there is reflected in the modal and in the list behind it, with the same error handling; otherwise the status is static.

### Filters
- AC-08: Given the list page, then the status and due-date filters are grouped in one bordered card labelled "Filters".
- AC-09: Given at least one filter is set, when the user chooses "Clear filters", then all filters are reset, the list is requested without them and shows page 1, and the page size is kept; given no filter is set, then the button is disabled.

### Header
- AC-10: Given a signed-in user, then the header shows the user's name on the right next to Log out; given the name is empty or unavailable, then the email is shown; given neither can be determined, then only Log out is shown. The header never blocks the page while the name loads.

## Edge cases
- Long titles wrap; they never push the actions out of the card.
- The title is a button that opens the view modal; it is keyboard operable and keeps the title as its accessible name.
- The tooltip is a small shared component (no library is installed) shown on hover and on keyboard focus, dismissed with Escape.
- Descriptions with line breaks are shown on one truncated line in the card and in full, with the breaks, in the view modal.
- Only one menu is open at a time; opening another closes the first.
- A status change from the tag or the modal disables the control while it is in flight, so it sends one request.
- Layout at 360px and 1280px has no horizontal scroll; the actions column does not overlap the text; targets are at least 36px.
- No console warnings or errors.

## API contract
No new endpoints. The user's name and email come from `GET /users` (already used by the assignee picker), matched on the signed-in user's id.

## AC -> test traceability
| AC | Test | Layer |
|---|---|---|
