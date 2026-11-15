import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render } from '@testing-library/react'
import type { ReactElement } from 'react'

export function createTestQueryClient() {
  return new QueryClient({ defaultOptions: { queries: { gcTime: 0 } } })
}

export function renderWithQuery(ui: ReactElement) {
  const client = createTestQueryClient()
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>)
}
