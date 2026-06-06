'use client';

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

type UserRole = 'client' | 'admin';

interface AuthUser {
  id: string;
  email: string;
  displayName: string;
  role: UserRole;
  emailVerified: boolean;
}

interface AuthStore {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  onboardingCompleted: boolean;
  login: (user: AuthUser) => void;
  loginAsNewUser: (user: AuthUser) => void;
  logout: () => void;
  setLoading: (loading: boolean) => void;
  completeOnboarding: () => void;
  reset: () => void;
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      onboardingCompleted: false,

      login: (user) =>
        set({
          user,
          isAuthenticated: true,
          isLoading: false,
          onboardingCompleted: true, // Existing user — already onboarded
        }),

      loginAsNewUser: (user) =>
        set({
          user,
          isAuthenticated: true,
          isLoading: false,
          onboardingCompleted: false, // New user — needs onboarding
        }),

      logout: () => {
        set({
          user: null,
          isAuthenticated: false,
          isLoading: false,
          onboardingCompleted: false,
        });
        // Clear other persisted stores on logout
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
