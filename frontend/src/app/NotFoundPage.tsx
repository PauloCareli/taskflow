import { Link } from 'react-router-dom'

export function NotFoundPage() {
  return (
    <section aria-labelledby="not-found-title" className="flex flex-col items-start gap-3">
      <h1 id="not-found-title" className="text-2xl font-semibold">
        Page not found
      </h1>
      <p className="text-fg-muted">The page you are looking for does not exist.</p>
      <Link to="/" className="text-accent-fg underline">
        Back to home
      </Link>
    </section>
  )
}
