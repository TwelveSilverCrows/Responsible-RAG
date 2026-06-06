'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/hooks/useAuth';
import { Loader2 } from 'lucide-react';

export default function Home() {
  const router = useRouter();
  const { isAuthenticated, onboardingCompleted, user } = useAuthStore();

  useEffect(() => {
    if (!isAuthenticated) {
      router.replace('/login');
      return;
    }

    if (!onboardingCompleted) {
      router.replace('/onboarding/welcome');
      return;
    }

    // Authenticated + onboarded → go to the right landing
    if (user?.role === 'admin') {
      router.replace('/admin');
    } else {
      router.replace('/chat');
    }
  }, [isAuthenticated, onboardingCompleted, user, router]);

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="flex items-center gap-2 text-muted-foreground text-sm">
        <Loader2 className="w-4 h-4 animate-spin" />
        Redirecting…
      </div>
    </div>
  );
}
