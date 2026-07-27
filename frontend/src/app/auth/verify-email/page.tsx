'use client';

import { useEffect, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { MailCheck } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { AuthLayout } from '@/components/layout/AuthLayout';

export default function VerifyEmailPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [isVerified, setIsVerified] = useState(false);

  useEffect(() => {
    if (searchParams.get('verified') === 'true') {
      setIsVerified(true);
    }
  }, [searchParams]);

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
              Your email has been verified. You can now sign in.
            </p>
          </div>
          <Button className="w-full" size="lg" onClick={() => navigate('/login')}>
            Go to sign in
          </Button>
        </div>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout>
      <div className="space-y-6 text-center">
        <div className="space-y-1.5">
          <h1 className="text-2xl font-display font-semibold">Check your email</h1>
          <p className="text-sm text-muted-foreground">
            We've sent a verification link to your email address.
            Click the link to activate your account, then sign in.
          </p>
        </div>
        <Link
          to="/login"
          className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          Back to sign in
        </Link>
      </div>
    </AuthLayout>
  );
}
