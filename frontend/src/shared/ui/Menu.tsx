import { useEffect, useRef, useState, type KeyboardEvent, type ReactNode } from 'react'

export type MenuItem = { label: string; onSelect: () => void; danger?: boolean }

type MenuProps = {
  /** Accessible name of the trigger and of the menu. */
  label: string
  items: MenuItem[]
  /** Visible content of the trigger button. */
  children: ReactNode
  triggerClassName?: string
  disabled?: boolean
}

export function Menu({ label, items, children, triggerClassName = '', disabled }: MenuProps) {
  const [open, setOpen] = useState(false)
  const root = useRef<HTMLDivElement>(null)
  const trigger = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    if (!open) return undefined
    root.current?.querySelector<HTMLElement>('[role="menuitem"]')?.focus()
    function onPointerDown(event: MouseEvent) {
      if (root.current && !root.current.contains(event.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', onPointerDown)
    return () => document.removeEventListener('mousedown', onPointerDown)
  }, [open])

  function entries(): HTMLElement[] {
    return [...(root.current?.querySelectorAll<HTMLElement>('[role="menuitem"]') ?? [])]
  }

  function onKeyDown(event: KeyboardEvent) {
    const all = entries()
    const index = all.indexOf(document.activeElement as HTMLElement)
    const move = (to: number) => {
      event.preventDefault()
      all[(to + all.length) % all.length]?.focus()
    }
    if (event.key === 'Escape') {
      event.stopPropagation()
      setOpen(false)
      trigger.current?.focus()
    } else if (event.key === 'ArrowDown') move(index + 1)
    else if (event.key === 'ArrowUp') move(index - 1)
    else if (event.key === 'Home') move(0)
    else if (event.key === 'End') move(all.length - 1)
    else if (event.key === 'Tab') setOpen(false)
  }

  function select(item: MenuItem) {
    // Focus goes back to the trigger first, so dialogs opened by the item return focus here.
    trigger.current?.focus()
    setOpen(false)
    item.onSelect()
  }

  return (
    <div ref={root} className="relative inline-block">
      <button
        ref={trigger}
        type="button"
        aria-label={label}
        aria-haspopup="menu"
        aria-expanded={open}
        disabled={disabled}
        onClick={() => setOpen((current) => !current)}
        className={`inline-flex min-h-9 items-center justify-center gap-1 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent disabled:cursor-not-allowed disabled:opacity-60 ${triggerClassName}`}
      >
        {children}
      </button>
      {open ? (
        <div
          role="menu"
          aria-label={label}
          tabIndex={-1}
          onKeyDown={onKeyDown}
          className="absolute right-0 z-20 mt-1 flex min-w-36 flex-col rounded-md border border-border bg-surface py-1 shadow-lg"
        >
          {items.map((item) => (
            <button
              key={item.label}
              type="button"
              role="menuitem"
              onClick={() => select(item)}
              className={`min-h-9 px-3 text-left text-sm hover:bg-canvas focus-visible:bg-canvas focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-accent ${item.danger ? 'text-danger' : 'text-fg'}`}
            >
              {item.label}
            </button>
          ))}
        </div>
      ) : null}
    </div>
  )
}
