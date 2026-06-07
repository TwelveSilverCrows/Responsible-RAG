'use client';

import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Loader2, Eye, EyeOff, Shield, UserPlus, Lock } from 'lucide-react';

import { useAuthStore } from '@/hooks/useAuth';
import { loginSchema, type LoginFormData } from '@/lib/schemas/profile.schema';
import { useProfileStore } from '@/stores/profileStore';
import { useConsentStore } from '@/stores/consentStore';
import { seedClientDemo, seedAdminDemo, seedGeneralDemo, clearDemoData } from '@/lib/demoSeeder';
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
  const profileStore = useProfileStore();
  const consentStore = useConsentStore();
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
    await new Promise((resolve) => setTimeout(resolve, 800));

    login({
      id: 'mock-user-1',
      email: data.email,
      displayName: data.email.split('@')[0],
      role: 'client',
      emailVerified: true,
    });

    // Seed general mode for email logins
    seedGeneralDemo({ profileStore, consentStore });

    navigate('/chat');
  }

  function handleGoogleLogin() {
    login({
      id: 'mock-google-user-1',
      email: 'user@gmail.com',
      displayName: 'Google User',
      role: 'client',
      emailVerified: true,
    });
    seedGeneralDemo({ profileStore, consentStore });
    navigate('/chat');
  }

  function handleDemoClientLogin() {
    login({
      id: 'demo-client',
      email: 'demo@responsible-ai.org',
      displayName: 'Alex',
      role: 'client',
      emailVerified: true,
    });
    seedClientDemo({ profileStore, consentStore });
    navigate('/chat');
  }

  function handleDemoAdminLogin() {
    login({
      id: 'demo-admin',
      email: 'admin@responsible-ai.org',
      displayName: 'Admin',
      role: 'admin',
      emailVerified: true,
    });
    seedAdminDemo({ profileStore, consentStore });
    navigate('/admin');
  }

  function handleDemoGeneralLogin() {
    login({
      id: 'demo-general',
      email: 'guest@responsible-ai.org',
      displayName: 'Guest',
      role: 'client',
      emailVerified: true,
    });
    seedGeneralDemo({ profileStore, consentStore });
    navigate('/chat');
  }

  function handleNewUserDemo() {
    loginAsNewUser({
      id: 'demo-new-user',
      email: 'newuser@responsible-ai.org',
      displayName: 'New User',
      role: 'client',
      emailVerified: false,
    });
    clearDemoData({ profileStore, consentStore });
    navigate('/onboarding/welcome');
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

      {/* Quick Demo Buttons */}
      <div className="bg-muted/50 rounded-lg p-4 space-y-3">
        <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider text-center">
          Quick Demo Access
        </p>
        <div className="grid grid-cols-2 gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleDemoClientLogin}
            className="w-full text-xs"
          >
            <span className="truncate">👤 Client (Full Profile)</span>
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleDemoAdminLogin}
            className="w-full text-xs"
          >
            <Shield className="w-3 h-3 mr-1" />
            <span className="truncate">Admin</span>
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleDemoGeneralLogin}
            className="w-full text-xs"
          >
            <Lock className="w-3 h-3 mr-1" />
            <span className="truncate">Client (General)</span>
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleNewUserDemo}
            className="w-full text-xs"
          >
            <UserPlus className="w-3 h-3 mr-1" />
            <span className="truncate">New User</span>
          </Button>
        </div>
        <p className="text-[10px] text-muted-foreground text-center">
          Skip sign-in and explore the app instantly. &quot;New User&quot; walks through onboarding.
        </p>
      </div>

      <GoogleOAuthButton mode="signin" onClick={handleGoogleLogin} />

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
