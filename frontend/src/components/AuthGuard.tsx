'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/hooks/useAuth';
import { Loader2 } from 'lucide-react';

/**
 * Redirects unauthenticated users to /login
 * Redirects authenticated but non-onboarded users to /onboarding/welcome
 */
export function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { isAuthenticated, onboardingCompleted } = useAuthStore();

  useEffect(() => {
    if (!isAuthenticated) {
      router.replace('/login');
    } else if (!onboardingCompleted) {
      router.replace('/onboarding/welcome');
    }
  }, [isAuthenticated, onboardingCompleted, router]);

  if (!isAuthenticated) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="flex items-center gap-2 text-muted-foreground text-sm">
          <Loader2 className="w-4 h-4 animate-spin" />
          Redirecting to login…
        </div>
      </div>
    );
  }

  if (!onboardingCompleted) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="flex items-center gap-2 text-muted-foreground text-sm">
          <Loader2 className="w-4 h-4 animate-spin" />
          Redirecting to onboarding…
        </div>
      </div>
    );
  }

  return <>{children}</>;
}

/**
 * Redirects non-admin users away from admin routes
 */
export function AdminGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { isAuthenticated, onboardingCompleted, user } = useAuthStore();

  useEffect(() => {
    if (!isAuthenticated) {
      router.replace('/login');
    } else if (!onboardingCompleted) {
      router.replace('/onboarding/welcome');
    } else if (user?.role !== 'admin') {
      router.replace('/chat');
    }
  }, [isAuthenticated, onboardingCompleted, user, router]);

  if (!isAuthenticated || !onboardingCompleted) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="flex items-center gap-2 text-muted-foreground text-sm">
          <Loader2 className="w-4 h-4 animate-spin" />
          Redirecting…
        </div>
      </div>
    );
  }

  if (user?.role !== 'admin') {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center space-y-4">
          <h1 className="text-2xl font-display font-semibold">Access Denied</h1>
          <p className="text-muted-foreground">You don't have permission to view this page.</p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}

/**
 * Redirects authenticated users away from auth pages (login/register)
 */
export function GuestGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { isAuthenticated, onboardingCompleted, user } = useAuthStore();

  useEffect(() => {
    if (isAuthenticated) {
      if (!onboardingCompleted) {
        router.replace('/onboarding/welcome');
      } else if (user?.role === 'admin') {
        router.replace('/admin');
      } else {
        router.replace('/chat');
      }
    }
  }, [isAuthenticated, onboardingCompleted, user, router]);

  if (isAuthenticated) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="flex items-center gap-2 text-muted-foreground text-sm">
          <Loader2 className="w-4 h-4 animate-spin" />
          Redirecting…
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
