import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'
import { ALICE, API, createApiMock, makeToken } from '../../../test/apiMock'
import { server } from '../../../test/server'
import { renderApp } from '../../../test/utils'
import { TOKEN_STORAGE_KEY } from './tokenStorage'

function useApi() {
  const mock = createApiMock()
  server.use(...mock.handlers)
  return mock
}

async function fillLogin(email: string, password: string) {
  await userEvent.type(await screen.findByLabelText(/email/i), email)
  await userEvent.type(screen.getByLabelText(/password/i), password)
  await userEvent.click(screen.getByRole('button', { name: /^sign in$/i }))
}

describe('sign in and session', () => {
  it('test_ac01_an_anonymous_user_is_redirected_to_login', async () => {
    useApi()
    renderApp('/')
    expect(await screen.findByRole('heading', { name: /sign in/i })).toBeInTheDocument()
  })

  it('test_ac01_valid_credentials_land_on_the_task_list', async () => {
    useApi()
    renderApp('/')
    await fillLogin(ALICE.email, ALICE.password)
    expect(await screen.findByRole('heading', { name: /^tasks$/i })).toBeInTheDocument()
    expect(localStorage.getItem(TOKEN_STORAGE_KEY)).toBeTruthy()
  })

  it('test_ac01_wrong_credentials_show_a_generic_error_and_stay_on_the_form', async () => {
    useApi()
    renderApp('/login')
    await fillLogin(ALICE.email, 'wrong-password')
    expect(await screen.findByRole('alert')).toHaveTextContent(/invalid email or password/i)
    expect(screen.getByRole('heading', { name: /sign in/i })).toBeInTheDocument()
    expect(localStorage.getItem(TOKEN_STORAGE_KEY)).toBeNull()
  })

  it('test_ac01_registering_signs_the_user_in_and_lands_on_the_task_list', async () => {
    const mock = useApi()
    renderApp('/register')
    await userEvent.type(await screen.findByLabelText(/name/i), 'Carol')
    await userEvent.type(screen.getByLabelText(/email/i), 'carol@example.com')
    await userEvent.type(screen.getByLabelText(/password/i), 'a-long-password')
    await userEvent.click(screen.getByRole('button', { name: /create account/i }))
    expect(await screen.findByRole('heading', { name: /^tasks$/i })).toBeInTheDocument()
    expect(mock.calls.slice(0, 2)).toEqual(['POST /auth/register', 'POST /auth/login'])
  })

  it('test_ac01_a_stored_token_keeps_the_session_after_a_reload', async () => {
    useApi()
    localStorage.setItem(TOKEN_STORAGE_KEY, makeToken(ALICE.id))
    renderApp('/')
    expect(await screen.findByRole('heading', { name: /^tasks$/i })).toBeInTheDocument()
  })

  it('test_ac01_an_expired_stored_token_is_dropped_and_asks_to_sign_in', async () => {
    useApi()
    localStorage.setItem(TOKEN_STORAGE_KEY, makeToken(ALICE.id, -60))
    renderApp('/')
    expect(await screen.findByRole('heading', { name: /sign in/i })).toBeInTheDocument()
    expect(localStorage.getItem(TOKEN_STORAGE_KEY)).toBeNull()
  })
})

describe('leaving the session', () => {
  it('test_ac02_a_401_from_the_api_discards_the_token_and_returns_to_login', async () => {
    useApi()
    localStorage.setItem(TOKEN_STORAGE_KEY, makeToken(ALICE.id))
    server.use(http.get(`${API}/tasks`, () => HttpResponse.json({}, { status: 401 })))
    renderApp('/')
    expect(await screen.findByRole('heading', { name: /sign in/i })).toBeInTheDocument()
    expect(localStorage.getItem(TOKEN_STORAGE_KEY)).toBeNull()
  })

  it('test_ac02_logout_discards_the_token_and_returns_to_login', async () => {
    useApi()
    localStorage.setItem(TOKEN_STORAGE_KEY, makeToken(ALICE.id))
    renderApp('/')
    await userEvent.click(await screen.findByRole('button', { name: /log out/i }))
    expect(await screen.findByRole('heading', { name: /sign in/i })).toBeInTheDocument()
    expect(localStorage.getItem(TOKEN_STORAGE_KEY)).toBeNull()
  })
})

describe('auth forms', () => {
  it('test_ac03_an_invalid_login_form_shows_field_errors_and_sends_nothing', async () => {
    const mock = useApi()
    renderApp('/login')
    await userEvent.type(await screen.findByLabelText(/email/i), 'not-an-email')
    await userEvent.click(screen.getByRole('button', { name: /^sign in$/i }))

    const email = screen.getByLabelText(/email/i)
    const password = screen.getByLabelText(/password/i)
    await waitFor(() => expect(email).toHaveAttribute('aria-invalid', 'true'))
    expect(password).toHaveAttribute('aria-invalid', 'true')
    expect(email).toHaveAccessibleDescription(/valid email/i)
    expect(password).toHaveAccessibleDescription(/password is required/i)
    expect(mock.calls).toEqual([])
  })

  it('test_ac03_an_invalid_register_form_shows_field_errors_and_sends_nothing', async () => {
    const mock = useApi()
    renderApp('/register')
    await userEvent.click(await screen.findByRole('button', { name: /create account/i }))
    await waitFor(() => expect(screen.getByLabelText(/name/i)).toHaveAttribute('aria-invalid', 'true'))
    expect(screen.getByLabelText(/email/i)).toHaveAttribute('aria-invalid', 'true')
    expect(screen.getByLabelText(/password/i)).toHaveAttribute('aria-invalid', 'true')
    expect(mock.calls).toEqual([])
  })

  it('test_ac03_a_taken_email_on_register_shows_the_api_message_on_the_form', async () => {
    useApi()
    renderApp('/register')
    await userEvent.type(await screen.findByLabelText(/name/i), 'Alice Again')
    await userEvent.type(screen.getByLabelText(/email/i), ALICE.email)
    await userEvent.type(screen.getByLabelText(/password/i), 'a-long-password')
    await userEvent.click(screen.getByRole('button', { name: /create account/i }))
    expect(await screen.findByRole('alert')).toHaveTextContent(/already registered/i)
    expect(screen.getByRole('heading', { name: /create account/i })).toBeInTheDocument()
  })

  it('test_ac03_a_422_on_register_shows_the_api_message_on_the_form', async () => {
    useApi()
    server.use(
      http.post(`${API}/auth/register`, () =>
        HttpResponse.json(
          { error: { code: 'validation_error', message: 'Password is too weak', details: [] } },
          { status: 422 },
        ),
      ),
    )
    renderApp('/register')
    await userEvent.type(await screen.findByLabelText(/name/i), 'Carol')
    await userEvent.type(screen.getByLabelText(/email/i), 'carol@example.com')
    await userEvent.type(screen.getByLabelText(/password/i), 'a-long-password')
    await userEvent.click(screen.getByRole('button', { name: /create account/i }))
    expect(await screen.findByRole('alert')).toHaveTextContent(/password is too weak/i)
  })
})
