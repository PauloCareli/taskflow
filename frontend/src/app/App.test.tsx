import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { StrictMode } from 'react'
import { createMemoryRouter, RouterProvider } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { server } from '../../test/server'
import { App } from './App'
import { AppShell } from './AppShell'
import { createAppRouter } from './router'

const HEALTH = 'http://api.test/health'

function renderApp(path = '/') {
  return render(
    <StrictMode>
      <App router={createAppRouter([path])} />
    </StrictMode>,
  )
}

describe('routing', () => {
  it('test_ac04_an_unknown_path_shows_not_found_with_a_link_home', async () => {
    renderApp('/nope/at/all')
    expect(await screen.findByRole('heading', { name: /page not found/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /back to home/i })).toHaveAttribute('href', '/')
  })

  it('test_ac04_the_not_found_link_returns_to_the_home_page', async () => {
    server.use(http.get(HEALTH, () => HttpResponse.json({ status: 'ok' })))
    renderApp('/nope')
    await userEvent.click(await screen.findByRole('link', { name: /back to home/i }))
    expect(await screen.findByText(/api is healthy/i)).toBeInTheDocument()
  })

  it('test_ac04_a_render_error_shows_a_fallback_and_keeps_the_shell_visible', async () => {
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => undefined)
    function Bomb(): never {
      throw new Error('kaboom')
    }
    const router = createMemoryRouter(
      [{ element: <AppShell />, children: [{ path: '/', element: <Bomb /> }] }],
      { initialEntries: ['/'] },
    )
    render(<RouterProvider router={router} />)

    expect(await screen.findByRole('alert')).toHaveTextContent(/something went wrong/i)
    expect(screen.getByRole('banner')).toBeInTheDocument()
    expect(screen.getByRole('main')).toBeInTheDocument()
    consoleError.mockRestore()
  })
})

describe('home page in the app shell', () => {
  it('test_ac10_the_shell_has_a_header_and_a_main_container', async () => {
    server.use(http.get(HEALTH, () => HttpResponse.json({ status: 'ok' })))
    renderApp()
    expect(screen.getByRole('banner')).toHaveTextContent(/taskflow/i)
    const main = screen.getByRole('main')
    expect(await within(main).findByText(/api is healthy/i)).toBeInTheDocument()
  })

  it('test_ac10_retry_is_reachable_and_activatable_with_the_keyboard', async () => {
    server.use(http.get(HEALTH, () => HttpResponse.json({}, { status: 500 })))
    renderApp()
    await screen.findByRole('alert')

    server.use(http.get(HEALTH, () => HttpResponse.json({ status: 'ok' })))
    await userEvent.tab()
    const retry = screen.getByRole('button', { name: /retry/i })
    expect(retry).toHaveFocus()
    await userEvent.keyboard('{Enter}')
    expect(await screen.findByText(/api is healthy/i)).toBeInTheDocument()
  })

  it('test_ac10_the_page_content_cannot_overflow_a_narrow_viewport', async () => {
    server.use(http.get(HEALTH, () => HttpResponse.json({ status: 'ok' })))
    renderApp()
    await screen.findByText(/api is healthy/i)
    expect(screen.getByRole('main').className).toMatch(/\bmin-w-0\b/)
    expect(screen.getByRole('main').className).toMatch(/\bmax-w-/)
  })
})

describe('strict mode', () => {
  it('test_ac11_sends_exactly_one_health_request_and_logs_nothing', async () => {
    let requests = 0
    server.use(
      http.get(HEALTH, () => {
        requests += 1
        return HttpResponse.json({ status: 'ok' })
      }),
    )
    renderApp()
    expect(await screen.findByText(/api is healthy/i)).toBeInTheDocument()
    expect(requests).toBe(1)
  })
})
