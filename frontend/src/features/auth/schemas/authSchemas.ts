import { z } from 'zod'

export const loginSchema = z.object({
  email: z.email({ error: 'Enter a valid email address' }),
  password: z.string().min(1, { error: 'Password is required' }),
})
export type LoginInput = z.infer<typeof loginSchema>

export const registerSchema = loginSchema.extend({
  name: z.string().trim().min(1, { error: 'Name is required' }),
})
export type RegisterInput = z.infer<typeof registerSchema>

export const tokenResponseSchema = z.object({
  access_token: z.string().min(1),
  token_type: z.string(),
  expires_in: z.number(),
})

export const registeredUserSchema = z.object({
  id: z.string(),
  email: z.string(),
  name: z.string(),
})

export const tokenClaimsSchema = z.object({
  sub: z.string().min(1),
  exp: z.number().optional(),
})
export type TokenClaims = z.infer<typeof tokenClaimsSchema>
