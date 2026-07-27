'use client';

import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/hooks/useAuth';
import { Loader2 } from 'lucide-react';

export default function Home() {
  const navigate = useNavigate();
  const { isAuthenticated, onboardingCompleted, user } = useAuthStore();

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login', { replace: true });
      return;
    }

    if (!onboardingCompleted) {
      navigate('/onboarding/welcome', { replace: true });
      return;
    }

    // Authenticated + onboarded → go to the right landing
    if (user?.role === 'admin') {
      navigate('/admin', { replace: true });
    } else {
      navigate('/chat', { replace: true });
    }
  }, [isAuthenticated, onboardingCompleted, user, navigate]);

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="flex items-center gap-2 text-muted-foreground text-sm">
        <Loader2 className="w-4 h-4 animate-spin" />
        Redirecting…
      </div>
    </div>
  );
}
