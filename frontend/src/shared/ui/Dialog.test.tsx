import { useState } from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { Dialog } from './Dialog'

function Harness({ onClose }: { onClose: () => void }) {
  return (
    <>
      <button>Open</button>
      <Dialog title="Edit" onClose={onClose}>
        <input aria-label="First" />
        <input aria-label="Second" />
      </Dialog>
    </>
  )
}

describe('dialog focus', () => {
  it('test_ac06_a_parent_rerender_with_a_new_onclose_does_not_move_focus', async () => {
    const { rerender } = render(<Harness onClose={() => undefined} />)
    expect(screen.getByLabelText('First')).toHaveFocus()
    await userEvent.click(screen.getByLabelText('Second'))
    rerender(<Harness onClose={() => undefined} />)
    expect(screen.getByLabelText('Second')).toHaveFocus()
  })

  it('test_ac06_closing_returns_focus_to_the_element_that_opened_it', async () => {
    function Page() {
      const [open, setOpen] = useState(false)
      return (
        <>
          <button onClick={() => setOpen(true)}>Open</button>
          {open ? <Harness onClose={() => setOpen(false)} /> : null}
        </>
      )
    }
    render(<Page />)
    const trigger = screen.getByRole('button', { name: 'Open' })
    await userEvent.click(trigger)
    await userEvent.keyboard('{Escape}')
    expect(trigger).toHaveFocus()
  })

  it('test_ac06_tab_wraps_inside_the_dialog_and_escape_calls_onclose', async () => {
    const onClose = vi.fn()
    render(
      <Dialog title="Edit" onClose={onClose}>
        <input aria-label="Only" />
      </Dialog>,
    )
    await userEvent.tab()
    expect(screen.getByLabelText('Only')).toHaveFocus()
    await userEvent.keyboard('{Escape}')
    expect(onClose).toHaveBeenCalledTimes(1)
  })
})
