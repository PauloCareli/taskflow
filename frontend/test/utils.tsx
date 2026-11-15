import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render } from '@testing-library/react'
import { StrictMode, type ReactElement } from 'react'
import { App } from '../src/app/App'
import { createAppRouter } from '../src/app/router'

export function createTestQueryClient() {
  return new QueryClient({ defaultOptions: { queries: { gcTime: 0 } } })
}

export function renderWithQuery(ui: ReactElement) {
  const client = createTestQueryClient()
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>)
}

export function renderApp(path = '/') {
  return render(
    <StrictMode>
      <App router={createAppRouter([path])} />
    </StrictMode>,
  )
}
