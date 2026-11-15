import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { Button } from '../../../shared/ui/Button'
import { TextField } from '../../../shared/ui/TextField'
import { SignInAfterRegisterError, useAuth } from '../hooks/AuthContext'
import { registerSchema, type RegisterInput } from '../schemas/authSchemas'

export function RegisterPage() {
  const { userId, register: signUp } = useAuth()
  const navigate = useNavigate()
  const [formError, setFormError] = useState<string | null>(null)
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegisterInput>({ resolver: zodResolver(registerSchema) })

  if (userId) return <Navigate to="/" replace />

  const onSubmit = handleSubmit(async (input) => {
    setFormError(null)
    try {
      await signUp(input)
    } catch (error) {
      if (error instanceof SignInAfterRegisterError) {
        void navigate('/login', { replace: true, state: { notice: error.message } })
        return
      }
      setFormError(error instanceof Error ? error.message : 'Could not create the account')
    }
  })

  return (
    <section
      aria-labelledby="register-title"
      className="mx-auto flex w-full max-w-sm flex-col gap-4"
    >
      <h1 id="register-title" className="text-2xl font-semibold">
        Create account
      </h1>
      <form onSubmit={onSubmit} noValidate className="flex flex-col gap-4">
        {formError ? (
          <p role="alert" className="text-sm text-danger">
            {formError}
          </p>
        ) : null}
        <TextField
          label="Name"
          autoComplete="name"
          error={errors.name?.message}
          {...register('name')}
        />
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
          autoComplete="new-password"
          error={errors.password?.message}
          {...register('password')}
        />
        <Button type="submit" disabled={isSubmitting}>
          Create account
        </Button>
      </form>
      <p className="text-sm text-fg-muted">
        Already registered?{' '}
        <Link to="/login" className="text-accent-fg underline">
          Sign in
        </Link>
      </p>
    </section>
  )
}
