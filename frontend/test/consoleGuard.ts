type Method = 'error' | 'warn'
type Target = Record<Method, (...args: never[]) => void>

const METHODS: Method[] = ['error', 'warn']

export function createConsoleGuard(target: Target) {
  const originals = { error: target.error, warn: target.warn }
  const calls: Method[] = []

  for (const method of METHODS) {
    target[method] = () => {
      calls.push(method)
    }
  }

  return {
    assertClean() {
      if (calls.length > 0) {
        const used = [...new Set(calls)].map((method) => `console.${method}`).join(' and ')
        throw new Error(`Test called ${used}; the console must stay clean.`)
      }
    },
    reset() {
      calls.length = 0
    },
    restore() {
      target.error = originals.error
      target.warn = originals.warn
    },
  }
}
