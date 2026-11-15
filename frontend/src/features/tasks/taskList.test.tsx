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

function openList(tasks: MockTask[] = []) {
  const mock = createApiMock({ tasks })
  server.use(...mock.handlers)
  localStorage.setItem(TOKEN_STORAGE_KEY, makeToken(ALICE.id))
  renderApp('/')
  return mock
}

const listCalls = (mock: ReturnType<typeof createApiMock>) =>
  mock.calls.filter((call) => call.startsWith('GET /tasks'))
const lastListCall = (mock: ReturnType<typeof createApiMock>) => listCalls(mock).at(-1) ?? ''

function manyTasks(count: number) {
  return Array.from({ length: count }, (_, index) => makeTask({ title: `Bulk ${index + 1}` }))
}

describe('task list states', () => {
  it('test_ac04_shows_loading_then_the_tasks_with_status_due_date_and_assignee', async () => {
    openList([
      makeTask({
        title: 'Write report',
        status: 'in_progress',
        due_date: '2099-03-05T12:00:00Z',
        assignee: { id: BOB.id, name: BOB.name },
      }),
    ])
    expect(await screen.findByRole('status')).toHaveTextContent(/loading tasks/i)
    const item = await screen.findByRole('listitem', { name: /write report/i })
    expect(within(item).getByText(/in progress/i)).toBeInTheDocument()
    expect(within(item).getByText(/mar 5, 2099/i)).toBeInTheDocument()
    expect(within(item).getByText(/bob/i)).toBeInTheDocument()
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
  })

  it('test_ac04_shows_an_empty_state_when_there_are_no_tasks', async () => {
    openList([])
    expect(await screen.findByText(/no tasks yet/i)).toBeInTheDocument()
    expect(screen.queryByRole('list')).not.toBeInTheDocument()
  })

  it('test_ac04_shows_an_error_with_a_retry_that_reloads_the_list', async () => {
    const mock = openList([makeTask({ title: 'Recovered task' })])
    server.use(
      http.get(`${API}/tasks`, () => HttpResponse.json({}, { status: 500 }), { once: true }),
    )
    expect(await screen.findByRole('alert')).toHaveTextContent(/could not load/i)
    await userEvent.click(screen.getByRole('button', { name: /retry/i }))
    expect(await screen.findByRole('listitem', { name: /recovered task/i })).toBeInTheDocument()
    expect(mock.calls.length).toBeGreaterThan(0)
  })

  it('test_ac04_marks_open_past_due_tasks_as_overdue_with_text', async () => {
    openList([
      makeTask({ title: 'Late open', due_date: '2020-01-01T00:00:00Z' }),
      makeTask({ title: 'Late done', status: 'completed', due_date: '2020-01-01T00:00:00Z' }),
      makeTask({ title: 'Late dropped', status: 'cancelled', due_date: '2020-01-01T00:00:00Z' }),
      makeTask({ title: 'Future', due_date: '2099-01-01T00:00:00Z' }),
    ])
    const late = await screen.findByRole('listitem', { name: /late open/i })
    expect(within(late).getByText(/overdue/i)).toBeInTheDocument()
    for (const name of [/late done/i, /late dropped/i, /future/i]) {
      expect(
        within(screen.getByRole('listitem', { name })).queryByText(/overdue/i),
      ).not.toBeInTheDocument()
    }
  })
})

describe('task list filters and paging', () => {
  it('test_ac05_choosing_statuses_requests_the_list_with_those_statuses', async () => {
    const mock = openList([
      makeTask({ title: 'Blocked one', status: 'blocked' }),
      makeTask({ title: 'Plain todo' }),
    ])
    await screen.findByRole('listitem', { name: /plain todo/i })
    await userEvent.click(screen.getByRole('checkbox', { name: /blocked/i }))
    await userEvent.click(screen.getByRole('checkbox', { name: /in progress/i }))
    await waitFor(() => {
      const params = new URLSearchParams(lastListCall(mock).split('?')[1])
      expect(params.getAll('status').sort()).toEqual(['blocked', 'in_progress'])
    })
    await waitFor(() =>
      expect(screen.queryByRole('listitem', { name: /plain todo/i })).not.toBeInTheDocument(),
    )
  })

  it('test_ac05_due_date_filters_are_sent_as_utc_start_and_end_of_day', async () => {
    const mock = openList([makeTask()])
    await screen.findByRole('listitem')
    await userEvent.type(screen.getByLabelText(/due after/i), '2030-01-10')
    await userEvent.type(screen.getByLabelText(/due before/i), '2030-02-20')
    await waitFor(() => {
      const call = decodeURIComponent(lastListCall(mock))
      expect(call).toContain('due_after=2030-01-10T00:00:00Z')
      expect(call).toContain('due_before=2030-02-20T23:59:59Z')
    })
  })

  it('test_ac05_changing_a_filter_resets_to_page_one', async () => {
    const mock = openList(manyTasks(30))
    await screen.findByRole('listitem', { name: /bulk 1$/i })
    await userEvent.click(screen.getByRole('button', { name: /next page/i }))
    await waitFor(() => expect(lastListCall(mock)).toContain('page=2'))
    await userEvent.click(screen.getByRole('checkbox', { name: /^to do$/i }))
    await waitFor(() => expect(lastListCall(mock)).toContain('status=todo'))
    expect(lastListCall(mock)).toContain('page=1')
  })

  it('test_ac05_next_and_previous_move_between_pages', async () => {
    const mock = openList(manyTasks(30))
    expect(await screen.findByText(/page 1 of 2/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /previous page/i })).toBeDisabled()
    await userEvent.click(screen.getByRole('button', { name: /next page/i }))
    expect(await screen.findByText(/page 2 of 2/i)).toBeInTheDocument()
    expect(lastListCall(mock)).toContain('page=2')
    expect(screen.getByRole('button', { name: /next page/i })).toBeDisabled()
    await userEvent.click(screen.getByRole('button', { name: /previous page/i }))
    expect(await screen.findByText(/page 1 of 2/i)).toBeInTheDocument()
  })

  it('test_ac05_the_page_size_defaults_to_25_and_changing_it_resets_to_page_one', async () => {
    const mock = openList(manyTasks(60))
    const size = await screen.findByLabelText(/page size/i)
    expect(size).toHaveValue('25')
    expect(listCalls(mock)[0]).toContain('size=25')
    await userEvent.click(screen.getByRole('button', { name: /next page/i }))
    await waitFor(() => expect(lastListCall(mock)).toContain('page=2'))
    await userEvent.selectOptions(size, '50')
    await waitFor(() => expect(lastListCall(mock)).toContain('size=50'))
    expect(lastListCall(mock)).toContain('page=1')
    expect(
      within(size)
        .getAllByRole('option')
        .map((option) => option.textContent),
    ).toEqual(['10', '25', '50', '100'])
  })
})
