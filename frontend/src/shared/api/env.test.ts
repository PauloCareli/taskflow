import { describe, expect, it } from 'vitest'
import { parseEnv } from './env'

describe('parseEnv', () => {
  it('test_ac07_accepts_http_and_https_urls', () => {
    expect(parseEnv({ VITE_API_BASE_URL: 'http://localhost:8000' }).apiBaseUrl).toBe(
      'http://localhost:8000',
    )
    expect(parseEnv({ VITE_API_BASE_URL: 'https://api.example.com' }).apiBaseUrl).toBe(
      'https://api.example.com',
    )
  })

  it('test_ac07_accepts_an_absolute_path', () => {
    expect(parseEnv({ VITE_API_BASE_URL: '/api' }).apiBaseUrl).toBe('/api')
  })

  it('test_ac07_trailing_slash_is_removed_and_path_prefix_is_kept', () => {
    expect(parseEnv({ VITE_API_BASE_URL: 'https://host/api/' }).apiBaseUrl).toBe('https://host/api')
    expect(parseEnv({ VITE_API_BASE_URL: '/api/' }).apiBaseUrl).toBe('/api')
  })

  it.each([
    ['missing', undefined],
    ['empty', ''],
    ['blank', '   '],
    ['relative path', 'api'],
    ['protocol-relative url', '//host/api'],
    ['unsupported scheme', 'ftp://host'],
    ['not a url', 'http//host'],
  ])('test_ac08_rejects_%s_value_with_a_clear_message', (_label, value) => {
    expect(() => parseEnv({ VITE_API_BASE_URL: value })).toThrow(
      /VITE_API_BASE_URL.*absolute http\(s\) URL or an absolute path/,
    )
  })
})
