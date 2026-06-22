/**
 * Route guard — redirect unauthenticated users to /auth (Phase 0.5).
 * Wrap protected routes with <RequireAuth>.
 */
import { Navigate } from 'react-router-dom';
import { getToken } from '../api/client';

export function RequireAuth({ children }: { children: React.ReactNode }) {
  const token = getToken();
  if (!token) return <Navigate to="/auth" replace />;
  return <>{children}</>;
}
