'use client';

import { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Loader2, ArrowLeft, MailCheck, RefreshCw } from 'lucide-react';

import { useAuthStore } from '@/hooks/useAuth';
import { Button } from '@/components/ui/button';
import { AuthLayout } from '@/components/layout/AuthLayout';

const COUNTDOWN_SECONDS = 60;

export default function VerifyEmailPage() {
  const navigate = useNavigate();
  const login = useAuthStore((s) => s.login);
  const [countdown, setCountdown] = useState(COUNTDOWN_SECONDS);
  const [isResending, setIsResending] = useState(false);
  const [isVerified, setIsVerified] = useState(false);

  useEffect(() => {
    if (countdown <= 0) return;

    const timer = setInterval(() => {
      setCountdown((prev) => prev - 1);
    }, 1000);

    return () => clearInterval(timer);
  }, [countdown]);

  const handleResend = useCallback(async () => {
    setIsResending(true);
    // Simulate resend
    await new Promise((resolve) => setTimeout(resolve, 1000));
    setIsResending(false);
    setCountdown(COUNTDOWN_SECONDS);
  }, []);

  function handleVerify() {
    // Mock verification — mark the user as verified
    const user = useAuthStore.getState().user;
    const token = useAuthStore.getState().token;
    if (user) {
      login({ ...user, emailVerified: true }, token ?? 'mock-token');
    }
    setIsVerified(true);
  }

  if (isVerified) {
    return (
      <AuthLayout>
        <div className="space-y-6 text-center">
          <div className="mx-auto w-12 h-12 rounded-full bg-teal-600/10 flex items-center justify-center">
            <MailCheck className="w-6 h-6 text-teal-600" />
          </div>
          <div className="space-y-1.5">
            <h1 className="text-2xl font-display font-semibold">Email verified!</h1>
            <p className="text-sm text-muted-foreground">
              Your email has been verified successfully. You&apos;re all set.
            </p>
          </div>
          <Button
            className="w-full"
            size="lg"
            onClick={() => navigate('/chat')}
          >
            Continue to chat
          </Button>
        </div>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout>
      <div className="space-y-6">
        <div className="space-y-1.5 text-center">
          <h1 className="text-2xl font-display font-semibold">Verify your email</h1>
          <p className="text-sm text-muted-foreground">
            We&apos;ve sent a verification email to your address. Please click the link to verify.
          </p>
        </div>

        <div className="space-y-3">
          <Button
            className="w-full"
            size="lg"
            onClick={handleVerify}
          >
            I&apos;ve verified my email
          </Button>

          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-border" />
            </div>
            <div className="relative flex justify-center text-xs">
              <span className="bg-card px-2 text-muted-foreground">
                or
              </span>
            </div>
          </div>

          <Button
            variant="outline"
            className="w-full"
            size="lg"
            disabled={countdown > 0 || isResending}
            onClick={handleResend}
          >
            {isResending ? (
              <>
                <Loader2 className="size-4 animate-spin" />
                Resending…
              </>
            ) : countdown > 0 ? (
              <>
                <RefreshCw className="size-4 opacity-50" />
                Resend email ({countdown}s)
              </>
            ) : (
              <>
                <RefreshCw className="size-4" />
                Resend verification email
              </>
            )}
          </Button>
        </div>

        <div className="text-center">
          <Link
            to="/login"
            className="inline-flex items-center gap-1.5 text-sm text-primary font-medium hover:text-primary/80"
          >
            <ArrowLeft className="size-4" />
            Back to sign in
          </Link>
        </div>
      </div>
    </AuthLayout>
  );
}
