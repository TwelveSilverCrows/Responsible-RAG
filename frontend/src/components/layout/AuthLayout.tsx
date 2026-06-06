'use client';

import { Shield } from 'lucide-react';

export function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <div className="w-full max-w-md">
        <div className="flex items-center justify-center gap-2 mb-8">
          <div className="w-10 h-10 rounded-lg bg-primary flex items-center justify-center">
            <Shield className="w-5 h-5 text-primary-foreground" />
          </div>
          <span className="text-xl font-display font-semibold">Responsible AI</span>
        </div>
        <div className="bg-card rounded-xl border shadow-sm p-8">
          {children}
        </div>
        <p className="text-center text-xs text-muted-foreground mt-6">
          By signing in, you agree to our{' '}
          <a href="#" className="text-primary underline underline-offset-2 hover:text-primary/80">
            Privacy Policy
          </a>
        </p>
      </div>
    </div>
  );
}
