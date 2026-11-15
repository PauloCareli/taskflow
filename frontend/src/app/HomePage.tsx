import { HealthStatus } from '../features/health/components/HealthStatus'

export function HomePage() {
  return (
    <section aria-labelledby="home-title" className="flex flex-col gap-4">
      <h1 id="home-title" className="text-2xl font-semibold">
        API status
      </h1>
      <HealthStatus />
    </section>
  )
}
