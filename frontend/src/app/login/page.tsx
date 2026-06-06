'use client';

import { AuthLayout } from '@/components/layout/AuthLayout';
import { LoginForm } from '@/components/auth/LoginForm';
import { GuestGuard } from '@/components/AuthGuard';

export default function LoginPage() {
  return (
    <GuestGuard>
      <AuthLayout>
        <LoginForm />
      </AuthLayout>
    </GuestGuard>
  );
}
