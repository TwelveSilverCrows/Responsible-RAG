'use client';

import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Loader2, Eye, EyeOff } from 'lucide-react';

import { useAuthStore } from '@/hooks/useAuth';
import { api } from '@/lib/api';
import { loginSchema, type LoginFormData } from '@/lib/schemas/profile.schema';
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

export function LoginForm() {
  const navigate = useNavigate();
  const login = useAuthStore((s) => s.login);
  const loginAsNewUser = useAuthStore((s) => s.loginAsNewUser);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const form = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: '',
      password: '',
    },
    mode: 'onTouched',
  });

  async function onSubmit(data: LoginFormData) {
    setIsSubmitting(true);
    try {
      const res = await api.auth.login({
        email: data.email,
        password: data.password,
      });

      // Decode JWT to get user info
      const payload = JSON.parse(atob(res.access_token.split('.')[1]));
      const role = payload.role === 'admin' ? 'admin' : 'user';
      const email = payload.sub || data.email;
      const needsOnboarding = payload.onboarding === true;

      if (needsOnboarding) {
        loginAsNewUser(
          { id: email, email, displayName: email.split('@')[0], role, emailVerified: true },
          res.access_token,
        );
        navigate('/onboarding/welcome', { replace: true });
      } else {
        login(
          { id: email, email, displayName: email.split('@')[0], role, emailVerified: true },
          res.access_token,
        );
        navigate(role === 'admin' ? '/admin' : '/chat');
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Login failed';
      form.setError('root', { message: msg });
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="space-y-1.5">
        <h1 className="text-2xl font-display font-semibold text-center">
          Welcome back
        </h1>
        <p className="text-sm text-muted-foreground text-center">
          Sign in to continue to Responsible AI
        </p>
      </div>
      <GoogleOAuthButton mode="signin" />

      <div className="relative">
        <Separator />
        <span className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 bg-card px-3 text-xs text-muted-foreground">
          or continue with email
        </span>
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

          <FormField
            control={form.control}
            name="password"
            render={({ field }) => (
              <FormItem>
                <div className="flex items-center justify-between">
                  <FormLabel>Password</FormLabel>
                  <Link
                    to="/auth/reset-password"
                    className="text-xs text-primary hover:text-primary/80 underline-offset-2 hover:underline"
                  >
                    Forgot password?
                  </Link>
                </div>
                <FormControl>
                  <div className="relative">
                    <Input
                      type={showPassword ? 'text' : 'password'}
                      placeholder="Enter your password"
                      autoComplete="current-password"
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
                <FormMessage />
              </FormItem>
            )}
          />

          {form.formState.errors.root && (
            <p className="text-sm text-destructive text-center">
              {form.formState.errors.root.message}
            </p>
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
                Signing in…
              </>
            ) : (
              'Sign in'
            )}
          </Button>
        </form>
      </Form>

      <p className="text-sm text-center text-muted-foreground">
        No account yet?{' '}
        <Link
          to="/register"
          className="text-primary font-medium hover:text-primary/80 underline-offset-2 hover:underline"
        >
          Create one
        </Link>
      </p>
    </div>
  );
}
