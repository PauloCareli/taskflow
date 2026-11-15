export type ApiErrorKind = 'http' | 'network' | 'timeout' | 'invalid_response'

type ApiErrorInit = {
  kind: ApiErrorKind
  code: string
  message: string
  status?: number
  details?: unknown[]
  cause?: unknown
}

export class ApiError extends Error {
  readonly kind: ApiErrorKind
  readonly code: string
  readonly status: number | undefined
  readonly details: unknown[]

  constructor({ kind, code, message, status, details = [], cause }: ApiErrorInit) {
    super(message, { cause })
    this.name = 'ApiError'
    this.kind = kind
    this.code = code
    this.status = status
    this.details = details
  }
}
