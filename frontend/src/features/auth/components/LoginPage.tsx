import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link, Navigate, useLocation } from 'react-router-dom'
import { Button } from '../../../shared/ui/Button'
import { TextField } from '../../../shared/ui/TextField'
import { useAuth } from '../hooks/AuthContext'
import { loginSchema, type LoginInput } from '../schemas/authSchemas'

export function LoginPage() {
  const { userId, login } = useAuth()
  const location = useLocation()
  const notice = (location.state as { notice?: string } | null)?.notice
  const [formError, setFormError] = useState<string | null>(null)
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginInput>({ resolver: zodResolver(loginSchema) })

  if (userId) return <Navigate to="/" replace />

  const onSubmit = handleSubmit(async (input) => {
    setFormError(null)
    try {
      await login(input)
    } catch (error) {
      setFormError(error instanceof Error ? error.message : 'Could not sign in')
    }
  })

  return (
    <section aria-labelledby="login-title" className="mx-auto flex w-full max-w-sm flex-col gap-4">
      <h1 id="login-title" className="text-2xl font-semibold">
        Sign in
      </h1>
      <form onSubmit={onSubmit} noValidate className="flex flex-col gap-4">
        {notice ? (
          <p role="status" className="text-sm text-fg-muted">
            {notice}
          </p>
        ) : null}
        {formError ? (
          <p role="alert" className="text-sm text-danger">
            {formError}
          </p>
        ) : null}
        <TextField
          label="Email"
          type="email"
          autoComplete="email"
          error={errors.email?.message}
          {...register('email')}
        />
        <TextField
          label="Password"
          type="password"
          autoComplete="current-password"
          error={errors.password?.message}
          {...register('password')}
        />
        <Button type="submit" disabled={isSubmitting}>
          Sign in
        </Button>
      </form>
      <p className="text-sm text-fg-muted">
        No account yet?{' '}
        <Link to="/register" className="text-accent-fg underline">
          Create one
        </Link>
      </p>
    </section>
  )
}
