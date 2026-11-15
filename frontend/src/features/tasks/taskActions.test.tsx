import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'
import {
  ALICE,
  API,
  BOB,
  createApiMock,
  makeTask,
  makeToken,
  type MockTask,
} from '../../../test/apiMock'
import { server } from '../../../test/server'
import { renderApp } from '../../../test/utils'
import { TOKEN_STORAGE_KEY } from '../auth/tokenStorage'

function openList(tasks: MockTask[], signedInAs = ALICE.id) {
  const mock = createApiMock({ tasks })
  server.use(...mock.handlers)
  localStorage.setItem(TOKEN_STORAGE_KEY, makeToken(signedInAs))
  renderApp('/')
  return mock
}

const item = (name: RegExp | string) => screen.findByRole('listitem', { name })
const writes = (mock: ReturnType<typeof createApiMock>) =>
  mock.calls.filter((call) => !call.startsWith('GET'))

async function openCreate() {
  await userEvent.click(await screen.findByRole('button', { name: /new task/i }))
  return screen.findByRole('dialog', { name: /new task/i })
}

function apiError(status: number, message: string) {
  return HttpResponse.json({ error: { code: 'x', message, details: [] } }, { status })
}

describe('task form', () => {
  it('test_ac06_invalid_create_input_shows_field_errors_and_sends_nothing', async () => {
    const mock = openList([])
    const dialog = await openCreate()
    const title = within(dialog).getByLabelText(/title/i)
    await userEvent.click(within(dialog).getByRole('button', { name: /create task/i }))
    await waitFor(() => expect(title).toHaveAttribute('aria-invalid', 'true'))
    expect(title).toHaveAccessibleDescription(/title is required/i)

    await userEvent.click(title)
    await userEvent.paste('x'.repeat(121))
    await userEvent.click(within(dialog).getByLabelText(/description/i))
    await userEvent.paste('y'.repeat(2001))
    await userEvent.type(within(dialog).getByLabelText(/due date/i), '2020-01-01')
    await userEvent.click(within(dialog).getByRole('button', { name: /create task/i }))
    await waitFor(() => expect(title).toHaveAccessibleDescription(/120 characters or fewer/i))
    expect(within(dialog).getByLabelText(/description/i)).toHaveAccessibleDescription(
      /2000 characters or fewer/i,
    )
    expect(within(dialog).getByLabelText(/due date/i)).toHaveAccessibleDescription(
      /cannot be in the past/i,
    )
    expect(writes(mock)).toEqual([])
  })

  it('test_ac06_a_valid_create_sends_the_task_and_the_list_shows_it', async () => {
    const mock = openList([])
    let body: unknown
    server.use(
      http.post(
        `${API}/tasks`,
        async ({ request }) => {
          body = await request.clone().json()
          return undefined
        },
        { once: true },
      ),
    )
    const dialog = await openCreate()
    // The assignee picker is populated from GET /users.
    const assignee = await within(dialog).findByLabelText(/assignee/i)
    await waitFor(() => expect(within(assignee).getAllByRole('option')).toHaveLength(3))
    await userEvent.type(within(dialog).getByLabelText(/title/i), 'Ship it')
    await userEvent.type(within(dialog).getByLabelText(/due date/i), '2099-12-31')
    await userEvent.selectOptions(assignee, 'Bob')
    await userEvent.click(within(dialog).getByRole('button', { name: /create task/i }))

    const created = await item(/ship it/i)
    expect(within(created).getByText(/assigned to bob/i)).toBeInTheDocument()
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(body).toEqual({
      title: 'Ship it',
      due_date: '2099-12-31T23:59:59Z',
      assignee_id: BOB.id,
    })
    expect(writes(mock)).toEqual(['POST /tasks'])
  })

  it('test_ac06_editing_sends_only_changed_fields_and_does_not_reject_a_past_due_date', async () => {
    const task = makeTask({ title: 'Old title', due_date: '2020-01-01T23:59:59Z' })
    const mock = openList([task])
    await userEvent.click(within(await item(/old title/i)).getByRole('button', { name: /edit/i }))
    const dialog = await screen.findByRole('dialog', { name: /edit task/i })
    const title = within(dialog).getByLabelText(/title/i)
    expect(title).toHaveValue('Old title')
    await userEvent.clear(title)
    await userEvent.type(title, 'New title')
    await userEvent.click(within(dialog).getByRole('button', { name: /save changes/i }))

    expect(await item(/new title/i)).toBeInTheDocument()
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(writes(mock)).toEqual([`PATCH /tasks/${task.id}`])
  })

  it('test_ac07_reassigning_from_the_edit_form_updates_the_assignee', async () => {
    const task = makeTask({ title: 'Hand over' })
    const mock = openList([task])
    await userEvent.click(within(await item(/hand over/i)).getByRole('button', { name: /edit/i }))
    const dialog = await screen.findByRole('dialog', { name: /edit task/i })
    const assignee = await within(dialog).findByLabelText(/assignee/i)
    await waitFor(() => expect(within(assignee).getAllByRole('option')).toHaveLength(3))
    await userEvent.selectOptions(assignee, 'Bob')
    await userEvent.click(within(dialog).getByRole('button', { name: /save changes/i }))

    expect(await screen.findByText(/assigned to bob/i)).toBeInTheDocument()
    expect(writes(mock)).toEqual([`POST /tasks/${task.id}/assign`])
  })

  it('test_ac06_submitting_twice_quickly_sends_one_request', async () => {
    const mock = openList([])
    const dialog = await openCreate()
    await userEvent.type(within(dialog).getByLabelText(/title/i), 'Once only')
    await userEvent.dblClick(within(dialog).getByRole('button', { name: /create task/i }))
    await item(/once only/i)
    expect(writes(mock)).toEqual(['POST /tasks'])
  })

  it('test_ac06_escape_closes_the_dialog_without_sending_anything', async () => {
    const mock = openList([])
    await openCreate()
    await userEvent.keyboard('{Escape}')
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(writes(mock)).toEqual([])
  })
})

describe('status, complete and permissions', () => {
  it('test_ac07_changing_the_status_updates_the_list_without_a_reload', async () => {
    const task = makeTask({ title: 'Move me' })
    const mock = openList([task])
    const card = await item(/move me/i)
    await userEvent.selectOptions(within(card).getByLabelText(/status/i), 'Blocked')
    await waitFor(() => expect(within(card).getByText('Blocked')).toBeInTheDocument())
    expect(writes(mock)).toEqual([`PATCH /tasks/${task.id}`])
  })

  it('test_ac07_completing_updates_the_list_and_removes_the_status_controls', async () => {
    const task = makeTask({ title: 'Finish me' })
    const mock = openList([task])
    const card = await item(/finish me/i)
    await userEvent.click(within(card).getByRole('button', { name: /complete/i }))
    await waitFor(() => expect(within(card).getByText('Completed')).toBeInTheDocument())
    expect(within(card).queryByRole('button', { name: /complete/i })).not.toBeInTheDocument()
    expect(within(card).queryByLabelText(/status/i)).not.toBeInTheDocument()
    expect(writes(mock)).toEqual([`POST /tasks/${task.id}/complete`])
  })

  it('test_ac07_an_assignee_can_change_status_but_not_edit_delete_or_assign', async () => {
    openList(
      [
        makeTask({
          title: 'Not mine',
          creator: { id: BOB.id, name: BOB.name },
          assignee: { id: ALICE.id, name: ALICE.name },
        }),
      ],
      ALICE.id,
    )
    const card = await item(/not mine/i)
    expect(within(card).getByLabelText(/status/i)).toBeInTheDocument()
    expect(within(card).getByRole('button', { name: /complete/i })).toBeInTheDocument()
    expect(within(card).queryByRole('button', { name: /edit/i })).not.toBeInTheDocument()
    expect(within(card).queryByRole('button', { name: /delete/i })).not.toBeInTheDocument()
  })

  it('test_ac07_terminal_tasks_offer_no_status_change', async () => {
    openList([makeTask({ title: 'Done already', status: 'completed' })])
    const card = await item(/done already/i)
    expect(within(card).queryByLabelText(/status/i)).not.toBeInTheDocument()
    expect(within(card).queryByRole('button', { name: /complete/i })).not.toBeInTheDocument()
  })

  it('test_ac07_a_409_shows_an_error_and_the_task_keeps_its_status', async () => {
    openList([makeTask({ title: 'Stuck' })])
    server.use(
      http.patch(`${API}/tasks/:id`, () => apiError(409, 'Invalid status transition'), {
        once: true,
      }),
    )
    const card = await item(/stuck/i)
    await userEvent.selectOptions(within(card).getByLabelText(/status/i), 'Blocked')
    expect(await screen.findByRole('alert')).toHaveTextContent(/invalid status transition/i)
    expect(within(await item(/stuck/i)).getByText('To do')).toBeInTheDocument()
  })

  it('test_ac07_a_403_shows_an_error_and_the_task_keeps_its_status', async () => {
    openList([makeTask({ title: 'Guarded' })])
    server.use(
      http.post(`${API}/tasks/:id/complete`, () => apiError(403, 'You cannot do that'), {
        once: true,
      }),
    )
    await userEvent.click(within(await item(/guarded/i)).getByRole('button', { name: /complete/i }))
    expect(await screen.findByRole('alert')).toHaveTextContent(/you cannot do that/i)
    expect(within(await item(/guarded/i)).getByText('To do')).toBeInTheDocument()
  })

  it('test_ac07_a_404_on_an_action_shows_an_error_and_refreshes_the_list', async () => {
    const mock = openList([makeTask({ title: 'Vanished' }), makeTask({ title: 'Stays' })])
    const card = await item(/vanished/i)
    mock.tasks.splice(0, 1)
    await userEvent.click(within(card).getByRole('button', { name: /complete/i }))
    expect(await screen.findByRole('alert')).toHaveTextContent(/not found/i)
    await waitFor(() =>
      expect(screen.queryByRole('listitem', { name: /vanished/i })).not.toBeInTheDocument(),
    )
    expect(screen.getByRole('listitem', { name: /stays/i })).toBeInTheDocument()
  })
})

describe('delete', () => {
  it('test_ac08_delete_asks_for_confirmation_and_cancel_sends_nothing', async () => {
    const mock = openList([makeTask({ title: 'Keep me' })])
    await userEvent.click(within(await item(/keep me/i)).getByRole('button', { name: /delete/i }))
    const dialog = await screen.findByRole('alertdialog', { name: /delete task/i })
    expect(dialog).toHaveTextContent(/keep me/i)
    await userEvent.click(within(dialog).getByRole('button', { name: /cancel/i }))
    expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument()
    expect(screen.getByRole('listitem', { name: /keep me/i })).toBeInTheDocument()
    expect(writes(mock)).toEqual([])
  })

  it('test_ac08_confirming_deletes_the_task_and_removes_it_from_the_list', async () => {
    const task = makeTask({ title: 'Remove me' })
    const mock = openList([task, makeTask({ title: 'Other' })])
    await userEvent.click(within(await item(/remove me/i)).getByRole('button', { name: /delete/i }))
    const dialog = await screen.findByRole('alertdialog')
    await userEvent.click(within(dialog).getByRole('button', { name: /^delete$/i }))
    await waitFor(() =>
      expect(screen.queryByRole('listitem', { name: /remove me/i })).not.toBeInTheDocument(),
    )
    expect(screen.getByRole('listitem', { name: /other/i })).toBeInTheDocument()
    expect(writes(mock)).toEqual([`DELETE /tasks/${task.id}`])
  })

  it('test_ac08_a_failed_delete_shows_an_error_and_leaves_the_list_unchanged', async () => {
    openList([makeTask({ title: 'Survivor' })])
    server.use(
      http.delete(`${API}/tasks/:id`, () => apiError(500, 'Server exploded'), { once: true }),
    )
    await userEvent.click(within(await item(/survivor/i)).getByRole('button', { name: /delete/i }))
    await userEvent.click(
      within(await screen.findByRole('alertdialog')).getByRole('button', { name: /^delete$/i }),
    )
    expect(await screen.findByRole('alert')).toHaveTextContent(/server exploded/i)
    expect(screen.getByRole('listitem', { name: /survivor/i })).toBeInTheDocument()
  })

  it('test_ac08_deleting_the_last_item_of_a_later_page_moves_to_the_previous_page', async () => {
    const tasks = Array.from({ length: 26 }, (_, index) => makeTask({ title: `Row ${index + 1}` }))
    openList(tasks)
    await item(/row 1$/i)
    await userEvent.click(screen.getByRole('button', { name: /next page/i }))
    const last = await item(/row 26/i)
    await userEvent.click(within(last).getByRole('button', { name: /delete/i }))
    await userEvent.click(
      within(await screen.findByRole('alertdialog')).getByRole('button', { name: /^delete$/i }),
    )
    expect(await screen.findByText(/page 1 of 1/i)).toBeInTheDocument()
    expect(await item(/row 1$/i)).toBeInTheDocument()
  })
})
