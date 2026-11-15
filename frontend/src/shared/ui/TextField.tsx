import { useId, type ComponentProps } from 'react'

type TextFieldProps = Omit<ComponentProps<'input'>, 'id'> & {
  label: string
  error?: string | undefined
}

export function TextField({ label, error, className = '', ...rest }: TextFieldProps) {
  const id = useId()
  const errorId = `${id}-error`
  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={id} className="text-sm font-medium">
        {label}
      </label>
      <input
        id={id}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? errorId : undefined}
        className={`min-h-9 rounded-md border border-border bg-surface px-3 text-sm text-fg focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent ${className}`}
        {...rest}
      />
      {error ? (
        <p id={errorId} className="text-sm text-danger">
          {error}
        </p>
      ) : null}
    </div>
  )
}
