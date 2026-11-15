import { useId } from 'react'
import { Button } from '../../../shared/ui/Button'

export const PAGE_SIZES = [10, 25, 50, 100] as const

type Props = {
  page: number
  size: number
  total: number
  onPage: (page: number) => void
  onSize: (size: number) => void
}

export function Pagination({ page, size, total, onPage, onSize }: Props) {
  const selectId = useId()
  const pages = Math.max(1, Math.ceil(total / size))
  return (
    <nav aria-label="Pagination" className="flex flex-wrap items-center gap-3">
      <Button variant="secondary" disabled={page <= 1} onClick={() => onPage(page - 1)}>
        Previous page
      </Button>
      <span className="text-sm">
        Page {page} of {pages}
      </span>
      <Button variant="secondary" disabled={page >= pages} onClick={() => onPage(page + 1)}>
        Next page
      </Button>
      <div className="ml-auto flex items-center gap-2 text-sm">
        <label htmlFor={selectId}>Page size</label>
        <select
          id={selectId}
          value={size}
          onChange={(event) => onSize(Number(event.target.value))}
          className="min-h-9 rounded-md border border-border bg-surface px-2 text-fg focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
        >
          {PAGE_SIZES.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      </div>
    </nav>
  )
}
