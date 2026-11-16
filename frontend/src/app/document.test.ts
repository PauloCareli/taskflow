import { existsSync, readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const root = resolve(__dirname, '../..')
const html = readFileSync(resolve(root, 'index.html'), 'utf8')

describe('the page document', () => {
  it('test_ac08_declares_an_icon_that_exists_so_the_browser_does_not_log_a_404', () => {
    const icon = /<link[^>]*rel="icon"[^>]*href="([^"]+)"/.exec(html)

    expect(icon).not.toBeNull()
    const href = (icon as RegExpExecArray)[1] as string
    expect(href.startsWith('/')).toBe(true)
    expect(existsSync(resolve(root, 'public', href.slice(1)))).toBe(true)
  })
})
