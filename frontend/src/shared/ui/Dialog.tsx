import { useEffect, useId, useRef, type ReactNode } from 'react'

type DialogProps = {
  title: string
  role?: 'dialog' | 'alertdialog'
  onClose: () => void
  /** Adds an X button and closes when the backdrop is clicked. */
  dismissible?: boolean
  children: ReactNode
}

const FOCUSABLE =
  'button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), a[href]'

export function Dialog({
  title,
  role = 'dialog',
  onClose,
  dismissible = false,
  children,
}: DialogProps) {
  const titleId = useId()
  const panel = useRef<HTMLDivElement>(null)
  const onCloseRef = useRef(onClose)

  useEffect(() => {
    onCloseRef.current = onClose
  })

  useEffect(() => {
    const previous = document.activeElement instanceof HTMLElement ? document.activeElement : null
    panel.current?.querySelector<HTMLElement>(FOCUSABLE)?.focus()

    function onKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        onCloseRef.current()
        return
      }
      if (event.key !== 'Tab' || !panel.current) return
      const items = [...panel.current.querySelectorAll<HTMLElement>(FOCUSABLE)]
      const first = items[0]
      const last = items.at(-1)
      if (!first || !last) return
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault()
        last.focus()
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault()
        first.focus()
      }
    }
    document.addEventListener('keydown', onKeyDown)
    return () => {
      document.removeEventListener('keydown', onKeyDown)
      previous?.focus()
    }
  }, [])

  return (
    <div
      role="presentation"
      className="fixed inset-0 z-10 flex items-center justify-center bg-canvas/80 p-4"
      onMouseDown={(event) => {
        if (dismissible && event.target === event.currentTarget) onClose()
      }}
    >
      <div
        ref={panel}
        role={role}
        aria-modal="true"
        aria-labelledby={titleId}
        className="flex max-h-full w-full max-w-md flex-col gap-4 overflow-y-auto rounded-md border border-border bg-surface p-6 shadow-lg"
      >
        <div className="flex items-start justify-between gap-2">
          <h2 id={titleId} className="min-w-0 break-words text-xl font-semibold">
            {title}
          </h2>
          {dismissible ? (
            <button
              type="button"
              aria-label="Close"
              onClick={onClose}
              className="-mr-2 -mt-1 inline-flex size-9 shrink-0 items-center justify-center rounded-md text-xl text-fg-muted hover:text-fg focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
            >
              <span aria-hidden="true">×</span>
            </button>
          ) : null}
        </div>
        {children}
      </div>
    </div>
  )
}
