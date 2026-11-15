import { Outlet } from 'react-router-dom'
import { useAuth } from '../features/auth/hooks/AuthContext'
import { Button } from '../shared/ui/Button'
import { ErrorBoundary } from '../shared/ui/ErrorBoundary'

export function AppShell() {
  const { userId, logout } = useAuth()
  return (
    <div className="flex min-h-screen flex-col bg-canvas text-fg">
      <header className="border-b border-border bg-surface">
        <div className="mx-auto flex h-14 w-full max-w-5xl items-center px-4">
          <span className="text-xl font-semibold">Taskflow</span>
          {userId ? (
            <Button variant="secondary" className="ml-auto" onClick={logout}>
              Log out
            </Button>
          ) : null}
        </div>
      </header>
      <main className="mx-auto w-full min-w-0 max-w-5xl flex-1 px-4 py-6">
        <ErrorBoundary>
          <Outlet />
        </ErrorBoundary>
      </main>
    </div>
  )
}
