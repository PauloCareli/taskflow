import { readdirSync, readFileSync, statSync } from 'node:fs'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { compile } from 'tailwindcss'
import { describe, expect, it } from 'vitest'

const here = dirname(fileURLToPath(import.meta.url))
const srcDir = resolve(here, '..')
const tokensCss = readFileSync(join(here, 'tokens.css'), 'utf8')
const indexCss = readFileSync(join(here, 'index.css'), 'utf8')

const TOKENS: Record<string, string> = {
  canvas: '#0d1117',
  surface: '#161b22',
  border: '#30363d',
  fg: '#e6edf3',
  'fg-muted': '#8b949e',
  accent: '#2f81f7',
  'accent-fg': '#58a6ff',
  success: '#3fb950',
  attention: '#d29922',
  danger: '#f85149',
}

function sourceFiles(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name)
    return statSync(path).isDirectory() ? sourceFiles(path) : [path]
  })
}

describe('design tokens', () => {
  it.each(Object.entries(TOKENS))('test_ac09_token_%s_is_defined_exactly_once', (name, hex) => {
    const definitions = tokensCss.match(new RegExp(`^\\s*--${name}:`, 'gm')) ?? []
    expect(definitions).toHaveLength(1)
    expect(tokensCss).toMatch(new RegExp(`--${name}:\\s*${hex}\\s*;`, 'i'))
  })

  it.each(Object.keys(TOKENS))('test_ac09_tailwind_theme_maps_%s_to_its_variable', (name) => {
    expect(indexCss).toMatch(new RegExp(`--color-${name}:\\s*var\\(--${name}\\)\\s*;`))
  })

  it('test_ac09_no_hardcoded_colors_outside_the_tokens_file', () => {
    const colorLiteral = /#[0-9a-f]{3,8}\b|\brgba?\(|\bhsla?\(/i
    const offenders = sourceFiles(srcDir)
      .filter((file) => /\.(css|ts|tsx)$/.test(file))
      .filter((file) => !file.endsWith('tokens.css') && !/\.test\.tsx?$/.test(file))
      .filter((file) => colorLiteral.test(readFileSync(file, 'utf8')))
    expect(offenders).toEqual([])
  })

  it('test_ac09_a_token_utility_resolves_to_the_token_variable', async () => {
    const compiler = await compile(indexCss, {
      base: here,
      loadStylesheet: async (id, base) => {
        const path = id === 'tailwindcss' ? 'tailwindcss/index.css' : id
        const file = id.startsWith('.')
          ? resolve(base, id)
          : resolve(here, '../../node_modules', path)
        return { path: file, base: dirname(file), content: readFileSync(file, 'utf8') }
      },
    })
    const css = compiler.build(['bg-accent', 'text-fg', 'border-border'])
    expect(css).toMatch(/background-color:\s*var\(--accent\)/)
    expect(css).toMatch(/color:\s*var\(--fg\)/)
    expect(css).toMatch(/border-color:\s*var\(--border\)/)
  })
})
