import { useEffect, useState, type ReactNode } from 'react'

type TooltipProps = { content: string; children: ReactNode }

/** Shows `content` in a bubble while the child is hovered or focused; Escape dismisses it. */
export function Tooltip({ content, children }: TooltipProps) {
  const [hovered, setHovered] = useState(false)
  const [focused, setFocused] = useState(false)
  const open = hovered || focused

  useEffect(() => {
    if (!open) return undefined
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        setHovered(false)
        setFocused(false)
      }
    }
    document.addEventListener('keydown', onKeyDown)
    return () => document.removeEventListener('keydown', onKeyDown)
  }, [open])

  return (
    <span
      className="relative block min-w-0"
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      onFocus={() => setFocused(true)}
      onBlur={() => setFocused(false)}
    >
      {children}
      {open ? (
        <span
          role="tooltip"
          className="absolute left-0 top-full z-20 mt-1 max-h-48 w-max max-w-xs overflow-y-auto whitespace-pre-wrap break-words rounded-md border border-border bg-surface p-2 text-sm text-fg shadow-lg"
        >
          {content}
        </span>
      ) : null}
    </span>
  )
}
