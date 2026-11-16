import { Outlet } from 'react-router-dom'
import { useAuth } from '../features/auth/hooks/AuthContext'
import { useUsers } from '../features/users/hooks/useUsers'
import { Button } from '../shared/ui/Button'
import { ErrorBoundary } from '../shared/ui/ErrorBoundary'

export function AppShell() {
  const { userId, logout } = useAuth()
  const users = useUsers({ enabled: userId !== null })
  const me = users.data?.find((user) => user.id === userId)
  const who = me?.name.trim() || me?.email
  return (
    <div className="flex min-h-screen flex-col bg-canvas text-fg">
      <header className="border-b border-border bg-surface">
        <div className="mx-auto flex h-14 w-full max-w-5xl items-center px-4">
          <span className="text-xl font-semibold">Taskflow</span>
          {userId ? (
            <div className="ml-auto flex min-w-0 items-center gap-3">
              {who ? <span className="min-w-0 truncate text-sm">{who}</span> : null}
              <Button variant="secondary" onClick={logout}>
                Log out
              </Button>
            </div>
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
