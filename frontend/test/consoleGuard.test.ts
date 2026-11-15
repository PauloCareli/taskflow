import { describe, expect, it } from 'vitest'
import { createConsoleGuard } from './consoleGuard'

function fakeConsole() {
  return {
    error: (message?: unknown) => void message,
    warn: (message?: unknown) => void message,
    log: (message?: unknown) => void message,
  }
}

describe('console guard', () => {
  it('test_ac12_console_error_makes_the_check_fail', () => {
    const target = fakeConsole()
    const guard = createConsoleGuard(target)
    target.error('boom')
    expect(() => guard.assertClean()).toThrow(/console\.error/)
    guard.restore()
  })

  it('test_ac12_console_warn_makes_the_check_fail', () => {
    const target = fakeConsole()
    const guard = createConsoleGuard(target)
    target.warn('careful')
    expect(() => guard.assertClean()).toThrow(/console\.warn/)
    guard.restore()
  })

  it('test_ac12_clean_run_passes_and_other_methods_are_ignored', () => {
    const target = fakeConsole()
    const guard = createConsoleGuard(target)
    target.log('fine')
    expect(() => guard.assertClean()).not.toThrow()
    guard.restore()
  })

  it('test_ac12_restore_puts_the_original_methods_back', () => {
    const target = fakeConsole()
    const originalError = target.error
    const guard = createConsoleGuard(target)
    expect(target.error).not.toBe(originalError)
    guard.restore()
    expect(target.error).toBe(originalError)
  })
})
