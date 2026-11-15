import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../hooks/AuthContext'

export function RequireAuth() {
  const { userId } = useAuth()
  return userId ? <Outlet /> : <Navigate to="/login" replace />
}
