import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { delay, http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'
import { server } from '../../../test/server'
import { renderWithQuery } from '../../../test/utils'
import { HealthStatus } from './components/HealthStatus'
import { healthSchema } from './schemas/healthSchema'

const URL = 'http://api.test/health'

function respondWith(counter: { count: number }, make: () => Response | Promise<Response>) {
  server.use(
    http.get(URL, () => {
      counter.count += 1
      return make()
    }),
  )
}

describe('health schema', () => {
  it('test_ac03_a_status_that_is_not_a_string_is_rejected', () => {
    expect(healthSchema.safeParse({ status: 123 }).success).toBe(false)
    expect(healthSchema.safeParse({}).success).toBe(false)
    expect(healthSchema.safeParse(null).success).toBe(false)
  })

  it('test_ac03_extra_fields_are_accepted_and_dropped', () => {
    expect(healthSchema.parse({ status: 'ok', version: '1' })).toEqual({ status: 'ok' })
  })
})

describe('HealthStatus', () => {
  it('test_ac01_shows_the_api_as_healthy_when_it_responds_ok', async () => {
    server.use(http.get(URL, () => HttpResponse.json({ status: 'ok' })))
    renderWithQuery(<HealthStatus />)
    expect(await screen.findByText(/api is healthy/i)).toBeInTheDocument()
    expect(screen.queryByText(/unavailable/i)).not.toBeInTheDocument()
  })

  it('test_ac02_shows_only_a_loading_state_while_the_request_is_in_flight', async () => {
    server.use(
      http.get(URL, async () => {
        await delay('infinite')
        return HttpResponse.json({ status: 'ok' })
      }),
    )
    renderWithQuery(<HealthStatus />)
    expect(await screen.findByText(/checking api status/i)).toBeInTheDocument()
    expect(screen.queryByText(/api is healthy/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/unavailable/i)).not.toBeInTheDocument()
  })

  it.each([
    [
      'a server error',
      () => HttpResponse.json({ error: { code: 'x', message: 'm' } }, { status: 500 }),
    ],
    ['a non-json 502', () => new HttpResponse('<h1>Bad gateway</h1>', { status: 502 })],
    ['a network failure', () => HttpResponse.error()],
    ['a body without a string status', () => HttpResponse.json({ status: 123 })],
    ['an empty 200 body', () => new HttpResponse(null, { status: 200 })],
  ])('test_ac03_shows_the_unavailable_error_for_%s', async (_label, make) => {
    const counter = { count: 0 }
    respondWith(counter, make)
    renderWithQuery(<HealthStatus />)
    expect(await screen.findByRole('alert')).toHaveTextContent(/api is unavailable/i)
    expect(screen.queryByText(/api is healthy/i)).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: /retry/i })).toBeEnabled()
  })

  it('test_ac03_a_failed_request_is_not_retried_automatically', async () => {
    const counter = { count: 0 }
    respondWith(counter, () => HttpResponse.json({}, { status: 500 }))
    renderWithQuery(<HealthStatus />)
    await screen.findByRole('alert')
    await delay(300)
    expect(counter.count).toBe(1)
  })

  it('test_ac03_retry_requests_again_without_reloading_and_recovers', async () => {
    const counter = { count: 0 }
    respondWith(counter, () => HttpResponse.json({}, { status: 500 }))
    renderWithQuery(<HealthStatus />)
    await screen.findByRole('alert')

    server.use(http.get(URL, () => HttpResponse.json({ status: 'ok' })))
    await userEvent.click(screen.getByRole('button', { name: /retry/i }))

    expect(await screen.findByText(/api is healthy/i)).toBeInTheDocument()
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })

  it('test_ac03_retry_while_a_request_is_in_flight_does_not_send_a_second_one', async () => {
    const counter = { count: 0 }
    respondWith(counter, () => HttpResponse.json({}, { status: 500 }))
    renderWithQuery(<HealthStatus />)
    await screen.findByRole('alert')
    expect(counter.count).toBe(1)

    respondWith(counter, async () => {
      await delay(200)
      return HttpResponse.json({ status: 'ok' })
    })
    const retry = screen.getByRole('button', { name: /retry/i })
    await userEvent.click(retry)
    await userEvent.click(retry)
    expect(await screen.findByText(/api is healthy/i)).toBeInTheDocument()
    expect(counter.count).toBe(2)
  })
})
