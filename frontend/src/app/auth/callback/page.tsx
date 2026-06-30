'use client';

import { useEffect, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuthStore, type AuthUser } from '@/hooks/useAuth';
import { api, type AuthUserDTO } from '@/lib/api';
import { Loader2 } from 'lucide-react';

/** Decode a JWT payload without verifying the signature. */
function decodeJwt(token: string): Record<string, unknown> {
  return JSON.parse(atob(token.split('.')[1]));
}

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

    (async () => {
      try {
        const payload = decodeJwt(token);
        const role: AuthUser['role'] = payload.role === 'admin' ? 'admin' : 'user';
        const email = (payload.sub as string) || '';

        // Temporarily store token so the api helper can read it for the /me call
        const tempUser: AuthUser = {
          id: email,
          email,
          displayName: email.split('@')[0],
          role,
          emailVerified: true,
        };

        if (isNew) {
          loginAsNewUser(tempUser, token);
        } else {
          login(tempUser, token);
        }

        // Fetch the real profile (includes name from Google / database)
        let displayName = email.split('@')[0];
        try {
          const profile: AuthUserDTO = await api.auth.me();
          displayName = profile.name || displayName;
        } catch {
          // /me may be unavailable for brand-new users; fall back gracefully
        }

        // Update the store with the real name
        const realUser: AuthUser = {
          id: email,
          email,
          displayName,
          role,
          emailVerified: true,
        };

        if (isNew) {
          loginAsNewUser(realUser, token);
          navigate('/onboarding/welcome', { replace: true });
        } else {
          login(realUser, token);
          navigate(role === 'admin' ? '/admin' : '/chat', { replace: true });
        }
      } catch {
        navigate('/login?error=invalid_token', { replace: true });
      }
    })();
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
