'use client';

import { AuthLayout } from '@/components/layout/AuthLayout';
import { RegisterForm } from '@/components/auth/RegisterForm';
import { GuestGuard } from '@/components/AuthGuard';

export default function RegisterPage() {
  return (
    <GuestGuard>
      <AuthLayout>
        <RegisterForm />
      </AuthLayout>
    </GuestGuard>
  );
}
