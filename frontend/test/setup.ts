import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterAll, afterEach, beforeAll, beforeEach } from 'vitest'
import { createConsoleGuard } from './consoleGuard'
import { server } from './server'

let guard: ReturnType<typeof createConsoleGuard>

beforeAll(() => server.listen({ onUnhandledFrame: 'error' }))
beforeEach(() => {
  guard = createConsoleGuard(console)
})
afterEach(() => {
  cleanup()
  server.resetHandlers()
  guard.restore()
  guard.assertClean()
})
afterAll(() => server.close())
