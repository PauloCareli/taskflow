import { delay, http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'
import { server } from '../../../test/server'
import { ApiError } from './ApiError'
import { createHttpClient } from './http'

const BASE = 'http://api.test'

function client(options: Partial<Parameters<typeof createHttpClient>[0]> = {}) {
  return createHttpClient({ baseUrl: BASE, timeoutMs: 1_000, ...options })
}

async function failure(promise: Promise<unknown>): Promise<ApiError> {
  try {
    await promise
  } catch (error) {
    if (error instanceof ApiError) return error
    throw error
  }
  throw new Error('expected the call to reject')
}

describe('http client: success', () => {
  it('test_ac05_resolves_with_the_parsed_json_body', async () => {
    server.use(http.get(`${BASE}/thing`, () => HttpResponse.json({ ok: true, n: 1 })))
    await expect(client().get('/thing')).resolves.toEqual({ ok: true, n: 1 })
  })

  it('test_ac05_sends_bearer_token_when_the_provider_returns_one', async () => {
    let header: string | null = 'unset'
    server.use(
      http.get(`${BASE}/thing`, ({ request }) => {
        header = request.headers.get('authorization')
        return HttpResponse.json({})
      }),
    )
    await client({ getToken: () => 'abc123' }).get('/thing')
    expect(header).toBe('Bearer abc123')
  })

  it.each([
    ['no provider', undefined],
    ['a provider returning null', () => null],
    ['a provider returning undefined', () => undefined],
  ])('test_ac05_omits_authorization_with_%s', async (_label, getToken) => {
    let header: string | null = 'unset'
    server.use(
      http.get(`${BASE}/thing`, ({ request }) => {
        header = request.headers.get('authorization')
        return HttpResponse.json({})
      }),
    )
    await client({ getToken }).get('/thing')
    expect(header).toBeNull()
  })
})

describe('http client: request url', () => {
  it.each([
    ['http://api.test', 'http://api.test/thing'],
    ['http://api.test/', 'http://api.test/thing'],
    ['http://api.test/v1', 'http://api.test/v1/thing'],
    ['http://api.test/v1/', 'http://api.test/v1/thing'],
  ])('test_ac07_base_%s_requests_%s', async (baseUrl, expected) => {
    let requested = ''
    server.use(
      http.get(expected, ({ request }) => {
        requested = request.url
        return HttpResponse.json({})
      }),
    )
    await client({ baseUrl }).get('/thing')
    expect(requested).toBe(expected)
  })

  it('test_ac07_a_path_only_base_is_resolved_against_the_page_origin', async () => {
    let requested = ''
    server.use(
      http.get('*/api/thing', ({ request }) => {
        requested = new URL(request.url).pathname
        return HttpResponse.json({})
      }),
    )
    await client({ baseUrl: '/api' }).get('/thing')
    expect(requested).toBe('/api/thing')
  })
})

describe('http client: failures become ApiError', () => {
  it('test_ac06_uniform_error_body_carries_status_code_message_and_details', async () => {
    server.use(
      http.get(`${BASE}/thing`, () =>
        HttpResponse.json(
          { error: { code: 'not_found', message: 'No such thing', details: [{ field: 'id' }] } },
          { status: 404 },
        ),
      ),
    )
    const error = await failure(client().get('/thing'))
    expect(error).toBeInstanceOf(ApiError)
    expect(error.kind).toBe('http')
    expect(error.status).toBe(404)
    expect(error.code).toBe('not_found')
    expect(error.message).toBe('No such thing')
    expect(error.details).toEqual([{ field: 'id' }])
  })

  it.each([
    ['missing', { error: { code: 'x', message: 'm' } }],
    ['null', { error: { code: 'x', message: 'm', details: null } }],
  ])('test_ac06_%s_details_become_an_empty_list', async (_label, body) => {
    server.use(http.get(`${BASE}/thing`, () => HttpResponse.json(body, { status: 400 })))
    const error = await failure(client().get('/thing'))
    expect(error.details).toEqual([])
  })

  it('test_ac06_unknown_extra_fields_in_the_error_body_are_ignored', async () => {
    server.use(
      http.get(`${BASE}/thing`, () =>
        HttpResponse.json(
          { error: { code: 'x', message: 'm', details: [], trace: 'secret' }, extra: 1 },
          { status: 400 },
        ),
      ),
    )
    const error = await failure(client().get('/thing'))
    expect(error.code).toBe('x')
    expect(error).not.toHaveProperty('trace')
  })

  it.each([
    ['an empty body', () => new HttpResponse(null, { status: 502 })],
    ['an html body', () => HttpResponse.html('<h1>Bad gateway</h1>', { status: 502 })],
    [
      'an invalid json body',
      () => new HttpResponse('{oops', { status: 502, headers: { 'content-type': 'text/plain' } }),
    ],
    ['a json body of another shape', () => HttpResponse.json({ detail: 'nope' }, { status: 502 })],
  ])('test_ac06_%s_maps_status_and_a_generic_message', async (_label, respond) => {
    server.use(http.get(`${BASE}/thing`, respond))
    const error = await failure(client().get('/thing'))
    expect(error.kind).toBe('http')
    expect(error.status).toBe(502)
    expect(error.code).toBe('http_error')
    expect(error.message).toMatch(/502/)
    expect(error.details).toEqual([])
  })

  it('test_ac06_a_network_failure_has_no_status', async () => {
    server.use(http.get(`${BASE}/thing`, () => HttpResponse.error()))
    const error = await failure(client().get('/thing'))
    expect(error.kind).toBe('network')
    expect(error.status).toBeUndefined()
    expect(error.code).toBe('network_error')
  })

  it('test_ac06_a_timeout_has_no_status_and_is_distinguishable_from_a_network_failure', async () => {
    server.use(
      http.get(`${BASE}/thing`, async () => {
        await delay('infinite')
        return HttpResponse.json({})
      }),
    )
    const error = await failure(client({ timeoutMs: 50 }).get('/thing'))
    expect(error.kind).toBe('timeout')
    expect(error.status).toBeUndefined()
    expect(error.code).toBe('timeout')
  })

  it('test_ac06_a_successful_response_that_is_not_json_is_an_error', async () => {
    server.use(http.get(`${BASE}/thing`, () => new HttpResponse('', { status: 200 })))
    const error = await failure(client().get('/thing'))
    expect(error.kind).toBe('invalid_response')
    expect(error.status).toBe(200)
  })
})
