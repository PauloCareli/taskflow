import { useEffect, useId, useRef, type ReactNode } from 'react'

type DialogProps = {
  title: string
  role?: 'dialog' | 'alertdialog'
  onClose: () => void
  children: ReactNode
}

const FOCUSABLE =
  'button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), a[href]'

export function Dialog({ title, role = 'dialog', onClose, children }: DialogProps) {
  const titleId = useId()
  const panel = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const previous = document.activeElement instanceof HTMLElement ? document.activeElement : null
    panel.current?.querySelector<HTMLElement>(FOCUSABLE)?.focus()

    function onKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        onClose()
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
  }, [onClose])

  return (
    <div className="fixed inset-0 z-10 flex items-center justify-center bg-canvas/80 p-4">
      <div
        ref={panel}
        role={role}
        aria-modal="true"
        aria-labelledby={titleId}
        className="flex max-h-full w-full max-w-md flex-col gap-4 overflow-y-auto rounded-md border border-border bg-surface p-6 shadow-lg"
      >
        <h2 id={titleId} className="text-xl font-semibold">
          {title}
        </h2>
        {children}
      </div>
    </div>
  )
}
