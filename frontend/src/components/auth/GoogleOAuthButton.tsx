'use client';

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { BASE_URL } from '@/lib/api';
import { Loader2 } from 'lucide-react';

interface GoogleOAuthButtonProps {
  mode?: 'signin' | 'signup';
  disabled?: boolean;
  className?: string;
}

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || '';

/**
 * Google OAuth button that redirects to the backend's /auth/google endpoint.
 * The backend handles the full OAuth code flow and redirects back to /auth/callback
 * with the JWT token in the URL.
 */
export function GoogleOAuthButton({
  mode,
  disabled,
  className,
}: GoogleOAuthButtonProps) {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const label = mode === 'signup' ? 'Sign up with Google' : 'Sign in with Google';

  function handleClick() {
    if (!GOOGLE_CLIENT_ID) return;
    setLoading(true);
    // Redirect to backend — it handles the full OAuth code flow
    window.location.href = `${BASE_URL}/auth/google`;
  }

  if (!GOOGLE_CLIENT_ID) {
    return (
      <Button
        type="button"
        variant="outline"
        size="lg"
        disabled
        className={cn(
          'w-full bg-white border-border text-foreground font-medium opacity-60',
          className
        )}
      >
        <svg className="size-5 shrink-0" viewBox="0 0 24 24" aria-hidden="true">
          <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4" />
          <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
          <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
          <path d="M12 5.38c1.02 0 1.94.35 2.66.93l2-2C15.73 2.59 13.99 2 12 2 7.7 2 3.99 4.47 2.18 7.07l2.85 2.22c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
        </svg>
        {label}
      </Button>
    );
  }

  return (
    <Button
      type="button"
      variant="outline"
      size="lg"
      disabled={disabled || loading}
      onClick={handleClick}
      className={cn(
        'w-full bg-white border-border hover:bg-secondary/50 text-foreground font-medium',
        className
      )}
    >
      {loading ? (
        <Loader2 className="w-5 h-5 mr-2 animate-spin" />
      ) : (
        <svg className="size-5 shrink-0" viewBox="0 0 24 24" aria-hidden="true">
          <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4" />
          <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
          <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
          <path d="M12 5.38c1.02 0 1.94.35 2.66.93l2-2C15.73 2.59 13.99 2 12 2 7.7 2 3.99 4.47 2.18 7.07l2.85 2.22c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
        </svg>
      )}
      {loading ? 'Redirecting to Google…' : label}
    </Button>
  );
}
