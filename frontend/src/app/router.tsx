import { createBrowserRouter, createMemoryRouter, type RouteObject } from 'react-router-dom'
import { AppShell } from './AppShell'
import { LoginPage } from '../features/auth/components/LoginPage'
import { RegisterPage } from '../features/auth/components/RegisterPage'
import { RequireAuth } from '../features/auth/components/RequireAuth'
import { TaskListPage } from '../features/tasks/components/TaskListPage'
import { HomePage } from './HomePage'
import { NotFoundPage } from './NotFoundPage'

export const routes: RouteObject[] = [
  {
    element: <AppShell />,
    children: [
      { path: '/login', element: <LoginPage /> },
      { path: '/register', element: <RegisterPage /> },
      { path: '/status', element: <HomePage /> },
      { element: <RequireAuth />, children: [{ path: '/', element: <TaskListPage /> }] },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
]

export function createAppRouter(initialEntries?: string[]) {
  return initialEntries
    ? createMemoryRouter(routes, { initialEntries })
    : createBrowserRouter(routes)
}
