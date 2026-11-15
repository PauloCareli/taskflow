# Frontend engineering rules

## Workflow
- Spec-driven: no code without ACs in the slice spec under `/spec`. Test first where behavior exists (red commit, green commit, refactor commit).
- Tests named after ACs; update the AC -> test table in the slice spec.

## Structure (`src/`)
```
app/        providers (QueryClient, Router, ErrorBoundary), routes, app shell
features/
  auth/     api/, components/, hooks/, schemas/
  tasks/    api/, components/, hooks/, schemas/
shared/
  api/      http client, ApiError, env
  ui/       presentational primitives (Button, Input, Badge, Dialog, ...)
  lib/      pure helpers (dates, formatting)
test/       setup, MSW handlers, test utils
```
- Features own their API calls, schemas, hooks and components. Features do not import each other's internals; share through `shared/`.
- `shared/ui` knows nothing about the domain.

## Rules
- **zod is the source of truth** for data shapes: define the schema, derive the type with `z.infer`. Parse every API response at the boundary; never trust the wire.
- **Server state lives in TanStack Query.** Do not copy it into `useState`, context or a store. Keep a query-key factory per feature; invalidate on mutations.
- **Local state** stays local: UI-only state in the component, lifted only when needed.
- **Forms**: react-hook-form + `zodResolver`; show field errors accessibly (`aria-invalid`, `aria-describedby`).
- **API client**: one module. Base URL from validated `import.meta.env`; maps the uniform error body to a typed `ApiError`; attaches the bearer token; handles 401 in one place.
- **Components**: small and focused; data fetching in hooks, rendering in components. Stable `key`s, no index keys for dynamic lists, effects only for synchronization (must survive StrictMode double-invocation).
- **TypeScript strict**: no `any`, no non-null assertions without a comment, no `@ts-ignore`.
- **Accessibility**: semantic elements, labelled controls, visible focus, keyboard operable, color is never the only signal.
- **No console output** (`console.*`) in app code; the browser console must stay clean.
- **Styling**: Tailwind utilities mapped to the tokens in `STYLE.md`; no hardcoded colors in components.
- **Handle every state**: loading, empty, error, success.

## Testing
- Vitest + React Testing Library + user-event + MSW. Query by role/label, assert user-visible behavior.
- A global setup fails any test that calls `console.error` or `console.warn`.
- Mock the network with MSW, never mock the app's own modules to make tests pass.
- Coverage reported; focus on feature flows over implementation details.

## Naming
- Components PascalCase files; hooks `useThing`; schemas `thingSchema` with type `Thing`; query keys `taskKeys`.
- Conventional commits with `Refs #n`.

## Definition of done
- [ ] ACs covered by tests named after them
- [ ] `just check` green (eslint, prettier check, tsc, vitest)
- [ ] No console warnings or errors in tests or in the browser for the touched flows
- [ ] Responsive at 360px and 1280px, keyboard usable
- [ ] README updated if commands, env vars or setup changed
- [ ] AI mistakes logged in `docs/ai/corrections.md`
