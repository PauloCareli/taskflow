import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useState } from 'react'
import { RouterProvider } from 'react-router-dom'
import { AuthProvider } from '../features/auth/components/AuthProvider'
import type { createAppRouter } from './router'

type AppProps = { router: ReturnType<typeof createAppRouter> }

export function App({ router }: AppProps) {
  const [queryClient] = useState(() => new QueryClient())
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <RouterProvider router={router} />
      </AuthProvider>
    </QueryClientProvider>
  )
}
