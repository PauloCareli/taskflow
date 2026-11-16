import { act, screen, waitFor, within } from '@testing-library/react'
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
import { chooseAction, chooseStatus, openActions } from '../../../test/ui'
import { renderApp } from '../../../test/utils'
import { TOKEN_STORAGE_KEY } from '../auth/tokenStorage'

function openList(tasks: MockTask[], signedInAs = ALICE.id) {
  const mock = createApiMock({ tasks })
  server.use(...mock.handlers)
  localStorage.setItem(TOKEN_STORAGE_KEY, makeToken(signedInAs))
  renderApp('/')
  return mock
}

const card = (name: RegExp | string) => screen.findByRole('listitem', { name })
const LONG = 'A very long description that goes on and on. '.repeat(10).trim()
const before = (first: Node, second: Node) =>
  Boolean(first.compareDocumentPosition(second) & Node.DOCUMENT_POSITION_FOLLOWING)

describe('task card content', () => {
  it('test_ac01_the_description_is_one_truncated_line_below_the_due_date_with_a_tooltip', async () => {
    openList([makeTask({ title: 'Wordy', description: LONG, due_date: '2099-03-05T12:00:00Z' })])
    const item = await card('Wordy')
    const description = within(item).getByText(LONG)
    expect(description.className).toMatch(/\btruncate\b/)
    expect(before(within(item).getByText(/due mar 5, 2099/i), description)).toBe(true)

    await userEvent.hover(description)
    expect(await screen.findByRole('tooltip')).toHaveTextContent(LONG)
    await userEvent.unhover(description)
    await waitFor(() => expect(screen.queryByRole('tooltip')).not.toBeInTheDocument())
  })

  it('test_ac01_the_tooltip_also_opens_on_keyboard_focus_and_closes_with_escape', async () => {
    openList([makeTask({ title: 'Focusable', description: LONG })])
    const item = await card('Focusable')
    const description = within(item).getByText(LONG)
    act(() => description.focus())
    expect(await screen.findByRole('tooltip')).toHaveTextContent(LONG)
    await userEvent.keyboard('{Escape}')
    expect(screen.queryByRole('tooltip')).not.toBeInTheDocument()
  })

  it('test_ac01_a_task_without_a_description_has_no_description_line', async () => {
    openList([makeTask({ title: 'Bare', description: null })])
    const item = await card('Bare')
    expect(within(item).queryByTestId('task-description')).not.toBeInTheDocument()
  })

  it('test_ac02_the_status_and_overdue_tags_come_below_the_description', async () => {
    openList([
      makeTask({ title: 'Late', description: 'Details', due_date: '2020-01-01T00:00:00Z' }),
    ])
    const item = await card('Late')
    const description = within(item).getByText('Details')
    const overdue = within(item).getByText(/overdue/i)
    const status = within(item).getByText('To do', { selector: 'span' })
    expect(before(description, status)).toBe(true)
    expect(before(description, overdue)).toBe(true)
    expect(overdue.className).toMatch(/rounded-full/)
  })
})

describe('card actions menu', () => {
  it('test_ac03_the_creator_has_view_edit_and_delete_in_the_menu_and_complete_beside_it', async () => {
    openList([makeTask({ title: 'Mine' })])
    const item = await card('Mine')
    expect(within(item).getByRole('button', { name: /^complete/i })).toBeInTheDocument()
    expect(within(item).queryByRole('button', { name: /^edit/i })).not.toBeInTheDocument()
    const menu = await openActions(item)
    expect(
      within(menu)
        .getAllByRole('menuitem')
        .map((entry) => entry.textContent),
    ).toEqual(['View', 'Edit', 'Delete'])
  })

  it('test_ac03_the_menu_opens_with_the_keyboard_moves_with_arrows_and_escape_returns_focus', async () => {
    openList([makeTask({ title: 'Keys' })])
    const item = await card('Keys')
    const kebab = within(item).getByRole('button', { name: /^actions for/i })
    expect(kebab).toHaveAttribute('aria-expanded', 'false')
    kebab.focus()
    await userEvent.keyboard('{Enter}')
    const menu = await screen.findByRole('menu')
    expect(kebab).toHaveAttribute('aria-expanded', 'true')
    const [view, edit] = within(menu).getAllByRole('menuitem')
    expect(view).toHaveFocus()
    await userEvent.keyboard('{ArrowDown}')
    expect(edit).toHaveFocus()
    await userEvent.keyboard('{Escape}')
    expect(screen.queryByRole('menu')).not.toBeInTheDocument()
    expect(kebab).toHaveFocus()
  })

  it('test_ac03_clicking_outside_closes_the_menu_and_opening_another_closes_the_first', async () => {
    openList([makeTask({ title: 'First' }), makeTask({ title: 'Second' })])
    const first = await card('First')
    const second = await card('Second')
    await openActions(first)
    await openActions(second)
    expect(screen.getAllByRole('menu')).toHaveLength(1)
    await userEvent.click(screen.getByRole('heading', { name: /^tasks$/i }))
    expect(screen.queryByRole('menu')).not.toBeInTheDocument()
  })

  it('test_ac03_the_menu_closes_after_choosing_an_action', async () => {
    openList([makeTask({ title: 'Closing' })])
    await chooseAction(await card('Closing'), /edit/i)
    expect(screen.queryByRole('menu')).not.toBeInTheDocument()
    expect(await screen.findByRole('dialog', { name: /edit task/i })).toBeInTheDocument()
  })
})

describe('status tag menu', () => {
  it('test_ac05_the_tag_shows_a_caret_and_lists_the_other_statuses_except_completed', async () => {
    openList([makeTask({ title: 'Switch', status: 'in_progress' })])
    const item = await card('Switch')
    const trigger = within(item).getByRole('button', { name: /change status/i })
    expect(trigger).toHaveAttribute('aria-haspopup', 'menu')
    expect(within(trigger).getByText('▾')).toBeInTheDocument()
    await userEvent.click(trigger)
    const menu = await screen.findByRole('menu')
    expect(
      within(menu)
        .getAllByRole('menuitem')
        .map((entry) => entry.textContent),
    ).toEqual(['To do', 'Blocked', 'Cancelled'])
  })

  it('test_ac05_choosing_a_status_updates_the_tag', async () => {
    openList([makeTask({ title: 'Tagged' })])
    const item = await card('Tagged')
    await chooseStatus(item, 'Blocked')
    await waitFor(() =>
      expect(within(item).getByText('Blocked', { selector: 'span' })).toBeInTheDocument(),
    )
  })

  it('test_ac05_the_tag_is_static_without_a_caret_when_the_status_cannot_change', async () => {
    openList([
      makeTask({ title: 'Closed', status: 'completed' }),
      makeTask({
        title: 'Not mine',
        creator: { id: BOB.id, name: BOB.name },
        assignee: null,
      }),
    ])
    const closed = await card('Closed')
    expect(within(closed).queryByRole('button', { name: /change status/i })).not.toBeInTheDocument()
    expect(within(closed).queryByText('▾')).not.toBeInTheDocument()
    expect(within(closed).getByText('Completed', { selector: 'span' })).toBeInTheDocument()
  })
})

describe('view modal', () => {
  it('test_ac06_view_from_the_menu_shows_the_task_read_only_and_x_closes_it', async () => {
    openList([
      makeTask({
        title: 'Inspect me',
        description: LONG,
        due_date: '2099-03-05T12:00:00Z',
        assignee: { id: BOB.id, name: BOB.name },
      }),
    ])
    const item = await card('Inspect me')
    await chooseAction(item, /view/i)
    const dialog = await screen.findByRole('dialog', { name: 'Inspect me' })
    expect(within(dialog).getByText(LONG)).toBeInTheDocument()
    expect(within(dialog).getByText(/mar 5, 2099/i)).toBeInTheDocument()
    expect(within(dialog).getByText(/created by alice/i)).toBeInTheDocument()
    expect(within(dialog).getByText(/assigned to bob/i)).toBeInTheDocument()
    expect(within(dialog).queryByRole('textbox')).not.toBeInTheDocument()
    await userEvent.click(within(dialog).getByRole('button', { name: 'Close' }))
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(within(item).getByRole('button', { name: /^actions for/i })).toHaveFocus()
  })

  it('test_ac06_clicking_the_title_opens_the_view_and_escape_and_outside_clicks_close_it', async () => {
    openList([makeTask({ title: 'Clickable' })])
    const item = await card('Clickable')
    const title = within(item).getByRole('button', { name: 'Clickable' })
    await userEvent.click(title)
    expect(await screen.findByRole('dialog', { name: 'Clickable' })).toBeInTheDocument()
    await userEvent.keyboard('{Escape}')
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(title).toHaveFocus()

    await userEvent.click(title)
    const dialog = await screen.findByRole('dialog')
    await userEvent.click(dialog.parentElement as HTMLElement)
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('test_ac07_the_modal_changes_status_and_completes_and_the_list_behind_follows', async () => {
    const mock = openList([makeTask({ title: 'From modal' })])
    const item = await card('From modal')
    await userEvent.click(within(item).getByRole('button', { name: 'From modal' }))
    const dialog = await screen.findByRole('dialog', { name: 'From modal' })
    await chooseStatus(dialog, 'Blocked')
    await waitFor(() =>
      expect(within(dialog).getByText('Blocked', { selector: 'span' })).toBeInTheDocument(),
    )
    expect(within(item).getByText('Blocked', { selector: 'span' })).toBeInTheDocument()
    await userEvent.click(within(dialog).getByRole('button', { name: /^complete/i }))
    await waitFor(() =>
      expect(within(dialog).getByText('Completed', { selector: 'span' })).toBeInTheDocument(),
    )
    expect(mock.calls.filter((call) => !call.startsWith('GET'))).toHaveLength(2)
  })

  it('test_ac07_the_modal_status_is_static_when_the_user_cannot_change_it', async () => {
    openList([makeTask({ title: 'Read only', status: 'cancelled' })])
    await userEvent.click(await screen.findByRole('button', { name: 'Read only' }))
    const dialog = await screen.findByRole('dialog', { name: 'Read only' })
    expect(within(dialog).queryByRole('button', { name: /change status/i })).not.toBeInTheDocument()
    expect(within(dialog).queryByRole('button', { name: /^complete/i })).not.toBeInTheDocument()
    expect(within(dialog).getByText('Cancelled', { selector: 'span' })).toBeInTheDocument()
  })
})

describe('menus and modal edge cases', () => {
  it('test_ac06_the_modal_stays_open_when_the_task_leaves_the_filtered_list', async () => {
    openList([makeTask({ title: 'Filtered out' }), makeTask({ title: 'Other', status: 'blocked' })])
    await userEvent.click(await screen.findByRole('checkbox', { name: /^to do$/i }))
    await waitFor(() =>
      expect(screen.queryByRole('listitem', { name: 'Other' })).not.toBeInTheDocument(),
    )
    await userEvent.click(await screen.findByRole('button', { name: 'Filtered out' }))
    const dialog = await screen.findByRole('dialog', { name: 'Filtered out' })
    await userEvent.click(within(dialog).getByRole('button', { name: /^complete/i }))
    await waitFor(() =>
      expect(screen.queryByRole('listitem', { name: 'Filtered out' })).not.toBeInTheDocument(),
    )
    expect(
      await within(screen.getByRole('dialog')).findByText('Completed', { selector: 'span' }),
    ).toBeInTheDocument()
  })

  it('test_ac06_a_task_that_no_longer_exists_closes_the_modal_with_a_message', async () => {
    const mock = openList([makeTask({ title: 'Gone soon' })])
    await userEvent.click(await screen.findByRole('button', { name: 'Gone soon' }))
    const dialog = await screen.findByRole('dialog', { name: 'Gone soon' })
    mock.tasks.splice(0, 1)
    await userEvent.click(within(dialog).getByRole('button', { name: /^complete/i }))
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
    expect(await screen.findByRole('alert')).toHaveTextContent(/not found/i)
  })

  it('test_ac03_tab_closes_the_menu', async () => {
    openList([makeTask({ title: 'Tabbing' })])
    await openActions(await card('Tabbing'))
    await userEvent.tab()
    expect(screen.queryByRole('menu')).not.toBeInTheDocument()
  })

  it('test_ac03_escape_in_a_menu_inside_the_modal_closes_only_the_menu', async () => {
    openList([makeTask({ title: 'Nested' })])
    await userEvent.click(await screen.findByRole('button', { name: 'Nested' }))
    const dialog = await screen.findByRole('dialog', { name: 'Nested' })
    await userEvent.click(within(dialog).getByRole('button', { name: /change status/i }))
    await screen.findByRole('menu')
    await userEvent.keyboard('{Escape}')
    expect(screen.queryByRole('menu')).not.toBeInTheDocument()
    expect(screen.getByRole('dialog', { name: 'Nested' })).toBeInTheDocument()
  })

  it('test_ac05_the_status_trigger_keeps_focus_and_a_36px_target_while_a_change_is_in_flight', async () => {
    openList([makeTask({ title: 'Focus stays' })])
    const item = await card('Focus stays')
    await chooseStatus(item, 'Blocked')
    const trigger = within(item).getByRole('button', { name: /change status/i })
    expect(trigger).toBeEnabled()
    expect(trigger.className).toMatch(/\bmin-h-9\b/)
    expect(trigger).toHaveFocus()
  })
})

describe('filters card and header', () => {
  it('test_ac08_filters_are_grouped_in_one_card_named_filters', async () => {
    openList([])
    const region = await screen.findByRole('region', { name: /^filters$/i })
    expect(within(region).getByRole('checkbox', { name: /blocked/i })).toBeInTheDocument()
    expect(within(region).getByLabelText(/due after/i)).toBeInTheDocument()
    expect(within(region).getByLabelText(/due before/i)).toBeInTheDocument()
    expect(region.className).toMatch(/\bborder\b/)
  })

  it('test_ac09_clear_filters_is_disabled_until_a_filter_is_set_then_resets_filters_and_page', async () => {
    const tasks = Array.from({ length: 60 }, (_, index) =>
      makeTask({ title: `Bulk ${index}`, due_date: '2099-01-01T00:00:00Z' }),
    )
    const mock = openList(tasks)
    const clear = await screen.findByRole('button', { name: /clear filters/i })
    expect(clear).toBeDisabled()
    await userEvent.selectOptions(await screen.findByLabelText(/page size/i), '10')
    await userEvent.click(screen.getByRole('checkbox', { name: /^to do$/i }))
    await userEvent.type(screen.getByLabelText(/due after/i), '2020-01-01')
    await userEvent.click(screen.getByRole('button', { name: /next page/i }))
    await waitFor(() => expect(mock.calls.at(-1)).toContain('page=2'))
    expect(clear).toBeEnabled()

    await userEvent.click(clear)
    await waitFor(() => {
      const last = mock.calls.at(-1) ?? ''
      expect(last).toContain('page=1')
      expect(last).toContain('size=10')
      expect(last).not.toContain('status=')
      expect(last).not.toContain('due_after')
    })
    expect(screen.getByRole('checkbox', { name: /^to do$/i })).not.toBeChecked()
    expect(screen.getByLabelText(/due after/i)).toHaveValue('')
    expect(clear).toBeDisabled()
  })

  it('test_ac10_the_header_shows_the_user_name_on_the_right', async () => {
    openList([])
    const header = await screen.findByRole('banner')
    expect(await within(header).findByText('Alice')).toBeInTheDocument()
    expect(within(header).getByRole('button', { name: /log out/i })).toBeInTheDocument()
  })

  it('test_ac10_the_header_falls_back_to_the_email_when_the_name_is_empty', async () => {
    openList([])
    server.use(
      http.get(`${API}/users`, () =>
        HttpResponse.json([{ id: ALICE.id, email: ALICE.email, name: '  ' }]),
      ),
    )
    const header = await screen.findByRole('banner')
    expect(await within(header).findByText(ALICE.email)).toBeInTheDocument()
  })

  it('test_ac10_the_header_shows_only_log_out_when_the_user_cannot_be_found', async () => {
    openList([])
    server.use(http.get(`${API}/users`, () => HttpResponse.json([])))
    const header = await screen.findByRole('banner')
    await screen.findByRole('heading', { name: /^tasks$/i })
    await waitFor(() => expect(within(header).queryByText('Alice')).not.toBeInTheDocument())
    expect(within(header).getByRole('button', { name: /log out/i })).toBeInTheDocument()
  })
})
