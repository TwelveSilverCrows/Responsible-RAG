'use client';

import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Loader2, ArrowLeft, Mail } from 'lucide-react';

import { resetPasswordSchema, type ResetPasswordFormData } from '@/lib/schemas/profile.schema';
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
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);

  const form = useForm<ResetPasswordFormData>({
    resolver: zodResolver(resetPasswordSchema),
    defaultValues: {
      email: '',
    },
    mode: 'onTouched',
  });

  async function onSubmit(data: ResetPasswordFormData) {
    setIsSubmitting(true);
    // Simulate network delay
    await new Promise((resolve) => setTimeout(resolve, 1000));
    setIsSubmitting(false);
    setIsSubmitted(true);
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
          <p className="text-xs text-muted-foreground">
            Didn&apos;t receive the email? Check your spam folder or{' '}
            <button
              type="button"
              className="text-primary underline underline-offset-2 hover:text-primary/80"
              onClick={() => {
                setIsSubmitted(false);
                form.reset();
              }}
            >
              try again
            </button>
          </p>
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
                    <Input
                      type="email"
                      placeholder="you@example.com"
                      autoComplete="email"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <Button
              type="submit"
              className="w-full"
              size="lg"
              disabled={isSubmitting}
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="size-4 animate-spin" />
                  Sending link…
                </>
              ) : (
                'Send reset link'
              )}
            </Button>
          </form>
        </Form>

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
