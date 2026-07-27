'use client';

import { useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Loader2, ArrowLeft, Mail, Lock, Eye, EyeOff } from 'lucide-react';

import { resetPasswordSchema, newPasswordSchema, type ResetPasswordFormData, type NewPasswordFormData } from '@/lib/schemas/profile.schema';
import { api } from '@/lib/api';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Form,
  FormField,
  FormItem,
  FormLabel,
  FormControl,
  FormMessage,
} from '@/components/ui/form';
import { AuthLayout } from '@/components/layout/AuthLayout';

export default function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const resetToken = searchParams.get('token');

  // ── Has token? Show set-new-password form ──────────────────────────────────
  if (resetToken) {
    return <SetNewPasswordForm token={resetToken} />;
  }

  // ── No token? Show forgot-password form ────────────────────────────────────
  return <ForgotPasswordForm />;
}

// ── Forgot password: request reset email ─────────────────────────────────────

function ForgotPasswordForm() {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);

  const form = useForm<ResetPasswordFormData>({
    resolver: zodResolver(resetPasswordSchema),
    defaultValues: { email: '' },
    mode: 'onTouched',
  });

  async function onSubmit(data: ResetPasswordFormData) {
    setIsSubmitting(true);
    try {
      await api.auth.forgotPassword(data.email);
      setIsSubmitted(true);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Request failed';
      toast.error(msg);
    } finally {
      setIsSubmitting(false);
    }
  }

  if (isSubmitted) {
    return (
      <AuthLayout>
        <div className="space-y-6 text-center">
          <div className="mx-auto w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center">
            <Mail className="w-6 h-6 text-primary" />
          </div>
          <div className="space-y-1.5">
            <h1 className="text-2xl font-display font-semibold">Check your email</h1>
            <p className="text-sm text-muted-foreground">
              If an account exists with that email, we&apos;ve sent a password reset link.
            </p>
          </div>
          <Link
            to="/login"
            className="inline-flex items-center gap-1.5 text-sm text-primary font-medium hover:text-primary/80"
          >
            <ArrowLeft className="size-4" />
            Back to sign in
          </Link>
        </div>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout>
      <div className="space-y-6">
        <div className="space-y-1.5">
          <h1 className="text-2xl font-display font-semibold text-center">
            Reset your password
          </h1>
          <p className="text-sm text-muted-foreground text-center">
            Enter your email and we&apos;ll send you a link to reset your password.
          </p>
        </div>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4" noValidate>
            <FormField
              control={form.control}
              name="email"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Email address</FormLabel>
                  <FormControl>
                    <Input type="email" placeholder="you@example.com" autoComplete="email" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <Button type="submit" className="w-full" size="lg" disabled={isSubmitting}>
              {isSubmitting ? (
                <><Loader2 className="size-4 animate-spin" /> Sending link…</>
              ) : 'Send reset link'}
            </Button>
          </form>
        </Form>

        <div className="text-center">
          <Link to="/login" className="inline-flex items-center gap-1.5 text-sm text-primary font-medium hover:text-primary/80">
            <ArrowLeft className="size-4" />
            Back to sign in
          </Link>
        </div>
      </div>
    </AuthLayout>
  );
}

// ── Set new password (from email link) ───────────────────────────────────────

function SetNewPasswordForm({ token }: { token: string }) {
  const navigate = useNavigate();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  const form = useForm<NewPasswordFormData>({
    resolver: zodResolver(newPasswordSchema),
    defaultValues: { password: '', confirmPassword: '' },
    mode: 'onTouched',
  });

  async function onSubmit(data: NewPasswordFormData) {
    setIsSubmitting(true);
    try {
      await api.auth.resetPassword(token, data.password);
      toast.success('Password reset successful! Sign in with your new password.');
      navigate('/login');
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Reset failed';
      toast.error(msg);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <AuthLayout>
      <div className="space-y-6">
        <div className="space-y-1.5">
          <div className="mx-auto w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center">
            <Lock className="w-6 h-6 text-primary" />
          </div>
          <h1 className="text-2xl font-display font-semibold text-center">Set new password</h1>
          <p className="text-sm text-muted-foreground text-center">Enter your new password below.</p>
        </div>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4" noValidate>
            <FormField
              control={form.control}
              name="password"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>New password</FormLabel>
                  <FormControl>
                    <div className="relative">
                      <Input type={showPassword ? 'text' : 'password'} placeholder="At least 8 characters" autoComplete="new-password" className="pr-10" {...field} />
                      <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground">
                        {showPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
                      </button>
                    </div>
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="confirmPassword"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Confirm password</FormLabel>
                  <FormControl>
                    <div className="relative">
                      <Input type={showConfirm ? 'text' : 'password'} placeholder="Re-enter your password" autoComplete="new-password" className="pr-10" {...field} />
                      <button type="button" onClick={() => setShowConfirm(!showConfirm)} className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground">
                        {showConfirm ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
                      </button>
                    </div>
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <Button type="submit" className="w-full" size="lg" disabled={isSubmitting}>
              {isSubmitting ? (
                <><Loader2 className="size-4 animate-spin" /> Resetting…</>
              ) : 'Reset password'}
            </Button>
          </form>
        </Form>
      </div>
    </AuthLayout>
  );
}
