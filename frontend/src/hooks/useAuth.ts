'use client';

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

type UserRole = 'client' | 'admin';

export interface AuthUser {
  id: string;
  email: string;
  displayName: string;
  role: UserRole;
  emailVerified: boolean;
}

interface AuthStore {
  user: AuthUser | null;
  token: string | undefined;
  refreshToken: string | undefined;
  isAuthenticated: boolean;
  isLoading: boolean;
  onboardingCompleted: boolean;
  login: (user: AuthUser, token: string, refreshToken?: string) => void;
  loginAsNewUser: (user: AuthUser, token: string, refreshToken?: string) => void;
  logout: () => void;
  setLoading: (loading: boolean) => void;
  completeOnboarding: () => void;
  reset: () => void;
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set) => ({
      user: null,
      token: undefined,
      refreshToken: undefined,
      isAuthenticated: false,
      isLoading: false,
      onboardingCompleted: false,

      login: (user, token, refreshToken) =>
        set({
          user,
          token,
          refreshToken,
          isAuthenticated: true,
          isLoading: false,
          onboardingCompleted: true,
        }),

      loginAsNewUser: (user, token, refreshToken) =>
        set({
          user,
          token,
          refreshToken,
          isAuthenticated: true,
          isLoading: false,
          onboardingCompleted: false,
        }),

      logout: () => {
        set({
          user: null,
          token: undefined,
          refreshToken: undefined,
          isAuthenticated: false,
          isLoading: false,
          onboardingCompleted: false,
        });
        if (typeof window !== 'undefined') {
          try {
            localStorage.removeItem('profile-store');
            localStorage.removeItem('consent-store');
            localStorage.removeItem('onboarding-step');
          } catch {
            // localStorage not available
          }
        }
      },

      setLoading: (isLoading) => set({ isLoading }),

      completeOnboarding: () => set({ onboardingCompleted: true }),

      reset: () =>
        set({
          user: null,
          token: undefined,
          refreshToken: undefined,
          isAuthenticated: false,
          isLoading: false,
          onboardingCompleted: false,
        }),
    }),
    { name: 'auth-store' }
  )
);

export function useAuth() {
  const store = useAuthStore();
  return {
    ...store,
    isAdmin: store.user?.role === 'admin',
    isClient: store.user?.role === 'client',
    isEmailVerified: store.user?.emailVerified ?? false,
    needsOnboarding: store.isAuthenticated && !store.onboardingCompleted,
  };
}
