import { Button } from '../../../shared/ui/Button'
import { useHealth } from '../hooks/useHealth'

export function HealthStatus() {
  const { data, isPending, isError, isFetching, refetch } = useHealth()

  if (isPending) {
    return (
      <p role="status" className="text-fg-muted">
        Checking API status…
      </p>
    )
  }

  if (isError) {
    return (
      <div className="flex flex-col items-start gap-3">
        <p role="alert" className="text-danger">
          The API is unavailable. Check that the backend is running and try again.
        </p>
        <Button variant="secondary" disabled={isFetching} onClick={() => void refetch()}>
          Retry
        </Button>
      </div>
    )
  }

  return (
    <p role="status" className={data.status === 'ok' ? 'text-success' : 'text-attention'}>
      {data.status === 'ok' ? 'The API is healthy.' : `The API reports status: ${data.status}.`}
    </p>
  )
}
