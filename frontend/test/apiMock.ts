import { http, HttpResponse } from 'msw'

export const API = 'http://api.test'

export type MockUser = { id: string; email: string; name: string; password: string }
export type MockTask = {
  id: string
  title: string
  description: string | null
  status: string
  due_date: string | null
  created_at: string
  updated_at: string
  completed_at: string | null
  creator: { id: string; name: string }
  assignee: { id: string; name: string } | null
}

export const ALICE: MockUser = {
  id: '11111111-1111-4111-8111-111111111111',
  email: 'alice@example.com',
  name: 'Alice',
  password: 'secret-pass',
}
export const BOB: MockUser = {
  id: '22222222-2222-4222-8222-222222222222',
  email: 'bob@example.com',
  name: 'Bob',
  password: 'secret-pass',
}

function base64url(value: object): string {
  return btoa(JSON.stringify(value)).replace(/=+$/, '').replace(/\+/g, '-').replace(/\//g, '_')
}

/** Unsigned JWT-shaped token; the API mock reads the `sub` claim. */
export function makeToken(userId: string, expiresInSeconds = 1800): string {
  const exp = Math.floor(Date.now() / 1000) + expiresInSeconds
  return `${base64url({ alg: 'HS256', typ: 'JWT' })}.${base64url({ sub: userId, exp })}.sig`
}

let counter = 0
export function makeTask(overrides: Partial<MockTask> = {}): MockTask {
  counter += 1
  const id = `00000000-0000-4000-8000-${String(counter).padStart(12, '0')}`
  return {
    id,
    title: `Task ${counter}`,
    description: null,
    status: 'todo',
    due_date: null,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    completed_at: null,
    creator: { id: ALICE.id, name: ALICE.name },
    assignee: null,
    ...overrides,
  }
}

const TERMINAL = ['completed', 'cancelled']

function error(status: number, code: string, message: string) {
  return HttpResponse.json({ error: { code, message, details: [] } }, { status })
}

/** In-memory API that follows the contracts of the auth and tasks issues. */
export function createApiMock(initial: { users?: MockUser[]; tasks?: MockTask[] } = {}) {
  const users = initial.users ?? [ALICE, BOB]
  const tasks = [...(initial.tasks ?? [])]
  const calls: string[] = []

  function userFrom(request: Request): MockUser | null {
    const header = request.headers.get('authorization')
    const token = header?.replace(/^Bearer /, '')
    const payload = token?.split('.')[1]
    if (!payload) return null
    try {
      const { sub } = JSON.parse(atob(payload.replace(/-/g, '+').replace(/_/g, '/'))) as {
        sub: string
      }
      return users.find((user) => user.id === sub) ?? null
    } catch {
      return null
    }
  }

  const unauthorized = () => error(401, 'unauthorized', 'Not authenticated')
  const visible = (task: MockTask, user: MockUser) =>
    task.creator.id === user.id || task.assignee?.id === user.id
  const brief = (id: string | null) => {
    const found = users.find((user) => user.id === id)
    return found ? { id: found.id, name: found.name } : null
  }

  const handlers = [
    http.post(`${API}/auth/register`, async ({ request }) => {
      calls.push('POST /auth/register')
      const body = (await request.json()) as { email: string; name: string; password: string }
      if (users.some((user) => user.email.toLowerCase() === body.email.toLowerCase())) {
        return error(409, 'email_taken', 'That email is already registered')
      }
      const user = { id: crypto.randomUUID(), ...body }
      users.push(user)
      return HttpResponse.json({ id: user.id, email: user.email, name: user.name }, { status: 201 })
    }),
    http.post(`${API}/auth/login`, async ({ request }) => {
      calls.push('POST /auth/login')
      const body = (await request.json()) as { email: string; password: string }
      const user = users.find(
        (candidate) =>
          candidate.email.toLowerCase() === body.email.toLowerCase() &&
          candidate.password === body.password,
      )
      if (!user) return error(401, 'invalid_credentials', 'Invalid email or password')
      return HttpResponse.json({
        access_token: makeToken(user.id),
        token_type: 'bearer',
        expires_in: 1800,
      })
    }),
    http.get(`${API}/users`, ({ request }) => {
      calls.push('GET /users')
      if (!userFrom(request)) return unauthorized()
      return HttpResponse.json(users.map(({ id, email, name }) => ({ id, email, name })))
    }),
    http.get(`${API}/tasks`, ({ request }) => {
      const url = new URL(request.url)
      calls.push(`GET /tasks${url.search}`)
      const user = userFrom(request)
      if (!user) return unauthorized()
      const page = Number(url.searchParams.get('page') ?? '1')
      const size = Number(url.searchParams.get('size') ?? '25')
      const statuses = url.searchParams.getAll('status')
      const before = url.searchParams.get('due_before')
      const after = url.searchParams.get('due_after')
      const matching = tasks.filter(
        (task) =>
          visible(task, user) &&
          (statuses.length === 0 || statuses.includes(task.status)) &&
          (!before || (task.due_date !== null && task.due_date <= before)) &&
          (!after || (task.due_date !== null && task.due_date >= after)),
      )
      const items = matching.slice((page - 1) * size, page * size)
      return HttpResponse.json({ items, total: matching.length, page, size })
    }),
    http.get(`${API}/tasks/:id`, ({ request, params }) => {
      calls.push(`GET /tasks/${String(params['id'])}`)
      const user = userFrom(request)
      if (!user) return unauthorized()
      const task = tasks.find((candidate) => candidate.id === params['id'])
      if (!task || !visible(task, user)) return error(404, 'not_found', 'Task not found')
      return HttpResponse.json(task)
    }),
    http.post(`${API}/tasks`, async ({ request }) => {
      calls.push('POST /tasks')
      const user = userFrom(request)
      if (!user) return unauthorized()
      const body = (await request.json()) as {
        title: string
        description?: string
        due_date?: string
        assignee_id?: string
      }
      const task = makeTask({
        title: body.title,
        description: body.description ?? null,
        due_date: body.due_date ?? null,
        creator: { id: user.id, name: user.name },
        assignee: brief(body.assignee_id ?? null),
      })
      tasks.push(task)
      return HttpResponse.json(task, { status: 201 })
    }),
    http.patch(`${API}/tasks/:id`, async ({ request, params }) => {
      calls.push(`PATCH /tasks/${String(params['id'])}`)
      const user = userFrom(request)
      if (!user) return unauthorized()
      const task = tasks.find((candidate) => candidate.id === params['id'])
      if (!task || !visible(task, user)) return error(404, 'not_found', 'Task not found')
      const body = (await request.json()) as Partial<MockTask>
      if (body.status !== undefined) {
        if (TERMINAL.includes(task.status)) {
          return error(409, 'invalid_transition', 'This task can no longer change status')
        }
      } else if (task.creator.id !== user.id) {
        return error(403, 'forbidden', 'Only the creator can edit this task')
      }
      Object.assign(task, body)
      return HttpResponse.json(task)
    }),
    http.post(`${API}/tasks/:id/assign`, async ({ request, params }) => {
      calls.push(`POST /tasks/${String(params['id'])}/assign`)
      const user = userFrom(request)
      if (!user) return unauthorized()
      const task = tasks.find((candidate) => candidate.id === params['id'])
      if (!task || !visible(task, user)) return error(404, 'not_found', 'Task not found')
      if (task.creator.id !== user.id) return error(403, 'forbidden', 'Only the creator can assign')
      const body = (await request.json()) as { assignee_id: string | null }
      task.assignee = brief(body.assignee_id)
      return HttpResponse.json(task)
    }),
    http.post(`${API}/tasks/:id/complete`, ({ request, params }) => {
      calls.push(`POST /tasks/${String(params['id'])}/complete`)
      const user = userFrom(request)
      if (!user) return unauthorized()
      const task = tasks.find((candidate) => candidate.id === params['id'])
      if (!task || !visible(task, user)) return error(404, 'not_found', 'Task not found')
      if (TERMINAL.includes(task.status)) {
        return error(409, 'invalid_transition', 'This task can no longer change status')
      }
      task.status = 'completed'
      task.completed_at = new Date().toISOString()
      return HttpResponse.json(task)
    }),
    http.delete(`${API}/tasks/:id`, ({ request, params }) => {
      calls.push(`DELETE /tasks/${String(params['id'])}`)
      const user = userFrom(request)
      if (!user) return unauthorized()
      const index = tasks.findIndex((candidate) => candidate.id === params['id'])
      const task = tasks[index]
      if (!task || !visible(task, user)) return error(404, 'not_found', 'Task not found')
      if (task.creator.id !== user.id) return error(403, 'forbidden', 'Only the creator can delete')
      tasks.splice(index, 1)
      return new HttpResponse(null, { status: 204 })
    }),
  ]

  return { handlers, tasks, users, calls }
}
