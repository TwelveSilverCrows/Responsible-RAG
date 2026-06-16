'use client';

import { useState, useMemo } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Loader2, Eye, EyeOff, ExternalLink } from 'lucide-react';

import { useAuthStore } from '@/hooks/useAuth';
import { registerSchema, type RegisterFormData } from '@/lib/schemas/profile.schema';
import { useConsentStore } from '@/stores/consentStore';
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
import { Separator } from '@/components/ui/separator';
import { GoogleOAuthButton } from '@/components/auth/GoogleOAuthButton';
import { cn } from '@/lib/utils';

function getPasswordStrength(password: string): {
  score: number;
  label: string;
  color: string;
} {
  let score = 0;
  if (password.length >= 8) score += 1;
  if (password.length >= 12) score += 1;
  if (/[A-Z]/.test(password)) score += 1;
  if (/[0-9]/.test(password)) score += 1;
  if (/[^A-Za-z0-9]/.test(password)) score += 1;

  if (score <= 2) return { score, label: 'Weak', color: 'bg-rose-500' };
  if (score <= 3) return { score, label: 'Medium', color: 'bg-amber-400' };
  return { score, label: 'Strong', color: 'bg-teal-600' };
}

export function RegisterForm() {
  const navigate = useNavigate();
  const loginAsNewUser = useAuthStore((s) => s.loginAsNewUser);
  const resetConsent = useConsentStore((s) => s.reset);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [devVerifyUrl, setDevVerifyUrl] = useState<string | null>(null);

  const form = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      displayName: '',
      email: '',
      password: '',
      confirmPassword: '',
    },
    mode: 'onTouched',
  });

  const passwordValue = form.watch('password');
  const strength = useMemo(() => getPasswordStrength(passwordValue ?? ''), [passwordValue]);

  async function onSubmit(data: RegisterFormData) {
    setIsSubmitting(true);
    try {
      const res = await api.auth.register({
        email: data.email,
        password: data.password,
        name: data.displayName,
      });

      toast.success('Account created!');
      
      // In dev mode, response includes a direct verification link
      const url = (res as any).dev_verify_url;
      if (url) {
        setDevVerifyUrl(url);
      } else {
        navigate('/login');
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Registration failed';
      form.setError('root', { message: msg });
    } finally {
      setIsSubmitting(false);
    }
  }

  function handleGoogleSignup() {
    // Google signup is handled by GoogleOAuthButton
  }

  return (
    <div className="space-y-6">
      <div className="space-y-1.5">
        <h1 className="text-2xl font-display font-semibold text-center">
          Create your account
        </h1>
        <p className="text-sm text-muted-foreground text-center">
          After registration, you&apos;ll set up your privacy preferences.
        </p>
      </div>

      <GoogleOAuthButton mode="signup" />

      <div className="relative">
        <Separator />
        <span className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 bg-card px-3 text-xs text-muted-foreground">
          or register with email
        </span>
      </div>

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4" noValidate>
          <FormField
            control={form.control}
            name="displayName"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Display name</FormLabel>
                <FormControl>
                  <Input
                    placeholder="What should we call you?"
                    autoComplete="name"
                    {...field}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

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

          <FormField
            control={form.control}
            name="password"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Password</FormLabel>
                <FormControl>
                  <div className="relative">
                    <Input
                      type={showPassword ? 'text' : 'password'}
                      placeholder="At least 8 characters"
                      autoComplete="new-password"
                      className="pr-10"
                      {...field}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                      aria-label={showPassword ? 'Hide password' : 'Show password'}
                    >
                      {showPassword ? (
                        <EyeOff className="size-4" />
                      ) : (
                        <Eye className="size-4" />
                      )}
                    </button>
                  </div>
                </FormControl>
                {passwordValue && passwordValue.length > 0 && (
                  <div className="space-y-1.5" aria-live="polite">
                    <div className="flex gap-1">
                      {[1, 2, 3, 4, 5].map((level) => (
                        <div
                          key={level}
                          className={cn(
                            'h-1.5 flex-1 rounded-full transition-colors',
                            strength.score >= level ? strength.color : 'bg-muted'
                          )}
                        />
                      ))}
                    </div>
                    <p
                      className={cn(
                        'text-xs',
                        strength.label === 'Weak' && 'text-rose-500',
                        strength.label === 'Medium' && 'text-amber-500',
                        strength.label === 'Strong' && 'text-teal-600'
                      )}
                    >
                      Password strength: {strength.label}
                    </p>
                  </div>
                )}
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
                    <Input
                      type={showConfirm ? 'text' : 'password'}
                      placeholder="Re-enter your password"
                      autoComplete="new-password"
                      className="pr-10"
                      {...field}
                    />
                    <button
                      type="button"
                      onClick={() => setShowConfirm(!showConfirm)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                      aria-label={showConfirm ? 'Hide password' : 'Show password'}
                    >
                      {showConfirm ? (
                        <EyeOff className="size-4" />
                      ) : (
                        <Eye className="size-4" />
                      )}
                    </button>
                  </div>
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          {form.formState.errors.root && (
            <div className="text-sm text-destructive bg-destructive/10 rounded-lg p-3">
              {form.formState.errors.root.message}
            </div>
          )}

          <Button
            type="submit"
            className="w-full"
            size="lg"
            disabled={isSubmitting}
          >
            {isSubmitting ? (
              <>
                <Loader2 className="size-4 animate-spin" />
                Creating account…
              </>
            ) : (
              'Create account'
            )}
          </Button>
        </form>
      </Form>

      {devVerifyUrl && (
        <div className="space-y-3 text-center">
          <div className="bg-muted/50 rounded-lg p-4 text-sm space-y-2">
            <p className="text-muted-foreground">
              No email sent (SMTP not configured).
            </p>
            <a
              href={devVerifyUrl}
              className="inline-flex items-center gap-1.5 text-primary font-medium hover:underline"
            >
              <ExternalLink className="size-4" />
              Click here to verify your email
            </a>
            <p className="text-xs text-muted-foreground">
              (This link appears only in dev mode)
            </p>
          </div>
          <Link
            to="/login"
            className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            Back to sign in
          </Link>
        </div>
      )}

      {!devVerifyUrl && (
        <p className="text-sm text-center text-muted-foreground">
          Already have an account?{' '}
          <Link
            to="/login"
            className="text-primary font-medium hover:text-primary/80 underline-offset-2 hover:underline"
          >
            Sign in
          </Link>
        </p>
      )}
    </div>
  );
}
