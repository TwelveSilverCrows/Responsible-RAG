'use client';

import { useEffect, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuthStore, type AuthUser } from '@/hooks/useAuth';
import { Loader2 } from 'lucide-react';

export default function AuthCallbackPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const login = useAuthStore((s) => s.login);
  const loginAsNewUser = useAuthStore((s) => s.loginAsNewUser);
  const calledRef = useRef(false);

  useEffect(() => {
    if (calledRef.current) return;
    calledRef.current = true;

    const token = searchParams.get('token');
    const isNew = searchParams.get('is_new') === 'true';
    if (!token) {
      navigate('/login?error=google_auth_failed', { replace: true });
      return;
    }

    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      const role: AuthUser['role'] = payload.role === 'admin' ? 'admin' : 'user';
      const email = payload.sub || '';

      const user: AuthUser = { id: email, email, displayName: email.split('@')[0], role, emailVerified: true };

      if (isNew) {
        loginAsNewUser(user, token);
        navigate('/onboarding/welcome', { replace: true });
      } else {
        login(user, token);
        navigate(role === 'admin' ? '/admin' : '/chat', { replace: true });
      }
    } catch {
      navigate('/login?error=invalid_token', { replace: true });
    }
  }, [searchParams, login, loginAsNewUser, navigate]);

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="flex items-center gap-2 text-muted-foreground text-sm">
        <Loader2 className="w-4 h-4 animate-spin" />
        Completing sign in…
      </div>
    </div>
  );
}
