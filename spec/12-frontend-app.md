# 12 - Frontend app

Issue: #12 · Depends on: 08-frontend-scaffold, API contracts of #9 (auth) and #10 (tasks) · Layers: frontend

## Goal
The usable product: a user signs in, then lists, filters, creates, edits, assigns, completes and deletes tasks. Server state comes from the API (mocked with MSW until the backend is merged); the UI is responsive, accessible and handles loading, empty, error and success states.

## Out of scope
- Profile editing, password reset, refresh tokens.
- Light theme.
- Sorting controls and filters beyond status and due date.

## Acceptance criteria

### Authentication
- AC-01: Given no valid session, when the user opens any task route, then they are redirected to the login page; given valid credentials on login, then they land on the task list; given a successful registration, then the user is signed in automatically and lands on the task list; given a stored token, when the page is reloaded, then the session is kept until the token expires; given wrong credentials, then a generic error is shown and the user stays on the form.
- AC-02: Given a signed-in user, when any API call returns 401 or the user chooses logout, then the token is removed from `localStorage`, cached server state is cleared and the user is taken to the login page.
- AC-03: Given the login or register form, when a field is invalid (empty or malformed email, empty password, empty name on register), then accessible field errors are shown (`aria-invalid`, `aria-describedby`) and no request is sent; given the API answers 409 on register (email taken) or 422, then the message is shown on the form.

### Task list
- AC-04: Given a signed-in user, when the task list loads, then it shows loading, then either the page of tasks (title, status, due date, assignee), an empty state, or an error state with retry; given a task is past due and neither completed nor cancelled, then it is marked overdue with text or icon in addition to color.
- AC-05: Given the status filter (one or more) and the due-date range filters, when the user changes any filter, then the list is re-requested with those filters and reset to page 1; given more than one page, then the user can move between pages and the current page is reflected in the request; the page size is chosen from a dropdown (default 25, max 100) and changing it resets to page 1. Date filters are date-only inputs read as UTC start and end of day.

### Task form and actions
- AC-06: Given the create or edit form, when the user submits invalid input (empty or over-120-char title, description over 2000 chars, due date in the past on create), then accessible field errors are shown and no request is sent; given valid input, then the task is created or updated and the list reflects it without a full reload; the assignee picker is populated from `GET /users`.
- AC-07: Given a task, when the user changes its status, completes it or reassigns it, then the list updates without a full reload; given a status change is not allowed (409) or forbidden (403), then an error message is shown and the task keeps its previous state; the current user is identified from the `sub` claim of the token, and only actions the user is permitted to perform are offered (creator: edit, delete, assign; creator or assignee: status).
- AC-08: Given a task, when the user chooses delete, then a confirmation dialog is shown first; on confirm the task is deleted and disappears from the list, on cancel nothing is sent; a failed mutation shows an error message and leaves the list unchanged.

## Edge cases
- Deleting the last item of a page other than the first moves to the previous page.
- A 404 on a task action (deleted elsewhere) shows an error and refreshes the list.
- Double submission of a form or action sends one request.
- Create and edit open in modal dialogs on the list; a due date in the past is rejected on create only. Routes: `/login`, `/register`, `/` (task list).
- The pages work at 360px and 1280px without horizontal scroll, are keyboard operable, and produce no console warnings or errors.

## API contract
Consumed as defined in #9 and #10 and the overview (error body, pagination `{items, total, page, size}`, 5 statuses).

| Method | Path | Request | Response | Errors |
|---|---|---|---|---|
| POST | `/auth/register` | `{email, name, password}` | `201 {id, email, name}` | 409, 422 |
| POST | `/auth/login` | `{email, password}` | `200 {access_token, token_type, expires_in}` | 401 |
| GET | `/users` | | `200 [{id, email, name}]` | 401 |
| GET | `/tasks` | `page`, `size`, `status`*, `due_before`, `due_after` | `200 {items, total, page, size}` | 401, 422 |
| POST | `/tasks` | `{title, description?, due_date?, assignee_id?}` | `201 Task` | 422 |
| PATCH | `/tasks/{id}` | `{title?, description?, due_date?, status?}` | `200 Task` | 403, 404, 409, 422 |
| DELETE | `/tasks/{id}` | | `204` | 403, 404 |
| POST | `/tasks/{id}/assign` | `{assignee_id: uuid \| null}` | `200 Task` | 403, 404, 422 |
| POST | `/tasks/{id}/complete` | | `200 Task` | 403, 404, 409 |

## AC -> test traceability
| AC | Test | Layer |
|---|---|---|
| AC-01 | `test_ac01_a_401_without_a_token_does_not_call_the_unauthorized_handler` (`src/shared/api/httpWrite.test.ts`) | frontend |
| AC-01 | `test_ac01_a_stored_token_keeps_the_session_after_a_reload` (`src/features/auth/auth.test.tsx`) | frontend |
| AC-01 | `test_ac01_an_anonymous_user_is_redirected_to_login` (`src/features/auth/auth.test.tsx`) | frontend |
| AC-01 | `test_ac01_an_expired_stored_token_is_dropped_and_asks_to_sign_in` (`src/features/auth/auth.test.tsx`) | frontend |
| AC-01 | `test_ac01_registering_signs_the_user_in_and_lands_on_the_task_list` (`src/features/auth/auth.test.tsx`) | frontend |
| AC-01 | `test_ac01_valid_credentials_land_on_the_task_list` (`src/features/auth/auth.test.tsx`) | frontend |
| AC-01 | `test_ac01_wrong_credentials_show_a_generic_error_and_stay_on_the_form` (`src/features/auth/auth.test.tsx`) | frontend |
| AC-02 | `test_ac02_a_401_from_the_api_discards_the_token_and_returns_to_login` (`src/features/auth/auth.test.tsx`) | frontend |
| AC-02 | `test_ac02_a_401_with_a_token_calls_the_unauthorized_handler_and_still_rejects` (`src/shared/api/httpWrite.test.ts`) | frontend |
| AC-02 | `test_ac02_logout_discards_the_token_and_returns_to_login` (`src/features/auth/auth.test.tsx`) | frontend |
| AC-03 | `test_ac03_a_422_on_register_shows_the_api_message_on_the_form` (`src/features/auth/auth.test.tsx`) | frontend |
| AC-03 | `test_ac03_a_taken_email_on_register_shows_the_api_message_on_the_form` (`src/features/auth/auth.test.tsx`) | frontend |
| AC-03 | `test_ac03_an_invalid_login_form_shows_field_errors_and_sends_nothing` (`src/features/auth/auth.test.tsx`) | frontend |
| AC-03 | `test_ac03_an_invalid_register_form_shows_field_errors_and_sends_nothing` (`src/features/auth/auth.test.tsx`) | frontend |
| AC-04 | `test_ac04_marks_open_past_due_tasks_as_overdue_with_text` (`src/features/tasks/taskList.test.tsx`) | frontend |
| AC-04 | `test_ac04_shows_an_empty_state_when_there_are_no_tasks` (`src/features/tasks/taskList.test.tsx`) | frontend |
| AC-04 | `test_ac04_shows_an_error_with_a_retry_that_reloads_the_list` (`src/features/tasks/taskList.test.tsx`) | frontend |
| AC-04 | `test_ac04_shows_loading_then_the_tasks_with_status_due_date_and_assignee` (`src/features/tasks/taskList.test.tsx`) | frontend |
| AC-05 | `test_ac05_changing_a_filter_resets_to_page_one` (`src/features/tasks/taskList.test.tsx`) | frontend |
| AC-05 | `test_ac05_choosing_statuses_requests_the_list_with_those_statuses` (`src/features/tasks/taskList.test.tsx`) | frontend |
| AC-05 | `test_ac05_due_date_filters_are_sent_as_utc_start_and_end_of_day` (`src/features/tasks/taskList.test.tsx`) | frontend |
| AC-05 | `test_ac05_next_and_previous_move_between_pages` (`src/features/tasks/taskList.test.tsx`) | frontend |
| AC-05 | `test_ac05_query_params_repeat_arrays_and_skip_empty_values` (`src/shared/api/httpWrite.test.ts`) | frontend |
| AC-05 | `test_ac05_the_page_size_defaults_to_25_and_changing_it_resets_to_page_one` (`src/features/tasks/taskList.test.tsx`) | frontend |
| AC-06 | `test_ac06_a_valid_create_sends_the_task_and_the_list_shows_it` (`src/features/tasks/taskActions.test.tsx`) | frontend |
| AC-06 | `test_ac06_editing_sends_only_changed_fields_and_does_not_reject_a_past_due_date` (`src/features/tasks/taskActions.test.tsx`) | frontend |
| AC-06 | `test_ac06_escape_closes_the_dialog_without_sending_anything` (`src/features/tasks/taskActions.test.tsx`) | frontend |
| AC-06 | `test_ac06_invalid_create_input_shows_field_errors_and_sends_nothing` (`src/features/tasks/taskActions.test.tsx`) | frontend |
| AC-06 | `test_ac06_post_sends_a_json_body_and_the_bearer_token` (`src/shared/api/httpWrite.test.ts`) | frontend |
| AC-06 | `test_ac06_submitting_twice_quickly_sends_one_request` (`src/features/tasks/taskActions.test.tsx`) | frontend |
| AC-07 | `test_ac07_a_403_shows_an_error_and_the_task_keeps_its_status` (`src/features/tasks/taskActions.test.tsx`) | frontend |
| AC-07 | `test_ac07_a_404_on_an_action_shows_an_error_and_refreshes_the_list` (`src/features/tasks/taskActions.test.tsx`) | frontend |
| AC-07 | `test_ac07_a_409_shows_an_error_and_the_task_keeps_its_status` (`src/features/tasks/taskActions.test.tsx`) | frontend |
| AC-07 | `test_ac07_an_assignee_can_change_status_but_not_edit_delete_or_assign` (`src/features/tasks/taskActions.test.tsx`) | frontend |
| AC-07 | `test_ac07_changing_the_status_updates_the_list_without_a_reload` (`src/features/tasks/taskActions.test.tsx`) | frontend |
| AC-07 | `test_ac07_completing_updates_the_list_and_removes_the_status_controls` (`src/features/tasks/taskActions.test.tsx`) | frontend |
| AC-07 | `test_ac07_patch_and_delete_use_their_methods_and_204_resolves_to_undefined` (`src/shared/api/httpWrite.test.ts`) | frontend |
| AC-07 | `test_ac07_reassigning_from_the_edit_form_updates_the_assignee` (`src/features/tasks/taskActions.test.tsx`) | frontend |
| AC-07 | `test_ac07_terminal_tasks_offer_no_status_change` (`src/features/tasks/taskActions.test.tsx`) | frontend |
| AC-08 | `test_ac08_a_failed_delete_shows_an_error_and_leaves_the_list_unchanged` (`src/features/tasks/taskActions.test.tsx`) | frontend |
| AC-08 | `test_ac08_confirming_deletes_the_task_and_removes_it_from_the_list` (`src/features/tasks/taskActions.test.tsx`) | frontend |
| AC-08 | `test_ac08_delete_asks_for_confirmation_and_cancel_sends_nothing` (`src/features/tasks/taskActions.test.tsx`) | frontend |
| AC-08 | `test_ac08_deleting_the_last_item_of_a_later_page_moves_to_the_previous_page` (`src/features/tasks/taskActions.test.tsx`) | frontend |
