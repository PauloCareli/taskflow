import { http, HttpResponse } from 'msw'
import { describe, expect, it, vi } from 'vitest'
import { server } from '../../../test/server'
import { ApiError } from './ApiError'
import { createHttpClient } from './http'

const BASE = 'http://api.test'

function client(options: Partial<Parameters<typeof createHttpClient>[0]> = {}) {
  return createHttpClient({ baseUrl: BASE, timeoutMs: 1_000, ...options })
}

describe('http client: writes and queries', () => {
  it('test_ac06_post_sends_a_json_body_and_the_bearer_token', async () => {
    let received: { body: unknown; auth: string | null; type: string | null } | undefined
    server.use(
      http.post(`${BASE}/tasks`, async ({ request }) => {
        received = {
          body: await request.json(),
          auth: request.headers.get('authorization'),
          type: request.headers.get('content-type'),
        }
        return HttpResponse.json({ id: 1 }, { status: 201 })
      }),
    )
    await expect(
      client({ getToken: () => 't0k' }).post('/tasks', { title: 'x' }),
    ).resolves.toEqual({ id: 1 })
    expect(received).toEqual({
      body: { title: 'x' },
      auth: 'Bearer t0k',
      type: 'application/json',
    })
  })

  it('test_ac07_patch_and_delete_use_their_methods_and_204_resolves_to_undefined', async () => {
    server.use(
      http.patch(`${BASE}/tasks/1`, () => HttpResponse.json({ ok: true })),
      http.delete(`${BASE}/tasks/1`, () => new HttpResponse(null, { status: 204 })),
    )
    await expect(client().patch('/tasks/1', { status: 'blocked' })).resolves.toEqual({ ok: true })
    await expect(client().delete('/tasks/1')).resolves.toBeUndefined()
  })

  it('test_ac05_query_params_repeat_arrays_and_skip_empty_values', async () => {
    let search = ''
    server.use(
      http.get(`${BASE}/tasks`, ({ request }) => {
        search = new URL(request.url).search
        return HttpResponse.json({})
      }),
    )
    await client().get('/tasks', {
      query: { page: 2, status: ['todo', 'blocked'], due_before: undefined, due_after: '' },
    })
    expect(search).toBe('?page=2&status=todo&status=blocked')
  })

  it('test_ac02_a_401_with_a_token_calls_the_unauthorized_handler_and_still_rejects', async () => {
    server.use(http.get(`${BASE}/tasks`, () => HttpResponse.json({}, { status: 401 })))
    const onUnauthorized = vi.fn()
    await expect(
      client({ getToken: () => 'old', onUnauthorized }).get('/tasks'),
    ).rejects.toBeInstanceOf(ApiError)
    expect(onUnauthorized).toHaveBeenCalledTimes(1)
  })

  it('test_ac01_a_401_without_a_token_does_not_call_the_unauthorized_handler', async () => {
    server.use(http.post(`${BASE}/auth/login`, () => HttpResponse.json({}, { status: 401 })))
    const onUnauthorized = vi.fn()
    await expect(client({ onUnauthorized }).post('/auth/login', {})).rejects.toBeInstanceOf(
      ApiError,
    )
    expect(onUnauthorized).not.toHaveBeenCalled()
  })
})
