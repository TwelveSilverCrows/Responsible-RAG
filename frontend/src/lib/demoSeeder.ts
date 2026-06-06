/**
 * Demo data seeder — populates Zustand stores with realistic mock data
 * so the app feels like a fully-working product during walkthrough.
 */
import type { UserProfile } from '@/types/profile';

// ── Full-profile "Alex" user ─────────────────────────────────
export const mockDemoProfile: UserProfile = {
  id: 'profile-demo-001',
  userId: 'demo-client',
  preferredName: 'Alex',
  ageRange: '31_50',
  genderIdentity: ['Non-binary'],
  pronouns: 'they/them',
  primaryLanguage: 'English',
  disability: ['cognitive'],
  immigrationStatus: 'permanent_resident',
  indigenousIdentity: 'non_indigenous',
  educationLevel: 'masters',
  literacyComfortAI: 4,
  profileMode: 'full',
  createdAt: new Date(Date.now() - 30 * 86400000).toISOString(),
  updatedAt: new Date().toISOString(),
};

// ── Full-profile "Admin" user ────────────────────────────────
export const mockAdminProfile: UserProfile = {
  id: 'profile-demo-admin',
  userId: 'demo-admin',
  preferredName: 'Admin',
  ageRange: '31_50',
  genderIdentity: ['Man'],
  pronouns: 'he/him',
  primaryLanguage: 'English',
  disability: [],
  immigrationStatus: 'citizen',
  indigenousIdentity: 'non_indigenous',
  educationLevel: 'doctoral',
  literacyComfortAI: 5,
  profileMode: 'full',
  createdAt: new Date(Date.now() - 60 * 86400000).toISOString(),
  updatedAt: new Date().toISOString(),
};

/**
 * Seed all stores for the client demo (full profile mode).
 * Call from LoginForm's "Client Demo" button.
 */
export function seedClientDemo(stores: {
  profileStore: { setProfile: (p: UserProfile) => void };
  consentStore: {
    setProfileMode: (m: 'full' | 'general') => void;
    setResearchDataConsent: (v: boolean) => void;
    setHasConsented: (v: boolean) => void;
  };
}) {
  stores.profileStore.setProfile(mockDemoProfile);
  stores.consentStore.setProfileMode('full');
  stores.consentStore.setResearchDataConsent(true);
  stores.consentStore.setHasConsented(true);
}

/**
 * Seed all stores for the admin demo (full profile mode).
 * Call from LoginForm's "Admin Demo" button.
 */
export function seedAdminDemo(stores: {
  profileStore: { setProfile: (p: UserProfile) => void };
  consentStore: {
    setProfileMode: (m: 'full' | 'general') => void;
    setResearchDataConsent: (v: boolean) => void;
    setHasConsented: (v: boolean) => void;
  };
}) {
  stores.profileStore.setProfile(mockAdminProfile);
  stores.consentStore.setProfileMode('full');
  stores.consentStore.setResearchDataConsent(true);
  stores.consentStore.setHasConsented(true);
}

/**
 * Seed stores for general-mode demo (no profile data).
 */
export function seedGeneralDemo(stores: {
  profileStore: { setProfile: (p: UserProfile | null) => void };
  consentStore: {
    setProfileMode: (m: 'full' | 'general') => void;
    setResearchDataConsent: (v: boolean) => void;
    setHasConsented: (v: boolean) => void;
  };
}) {
  stores.profileStore.setProfile(null);
  stores.consentStore.setProfileMode('general');
  stores.consentStore.setResearchDataConsent(false);
  stores.consentStore.setHasConsented(true);
}

/**
 * Clear all demo data — used when starting the new-user onboarding flow.
 */
export function clearDemoData(stores: {
  profileStore: { reset: () => void };
  consentStore: { reset: () => void };
}) {
  stores.profileStore.reset();
  stores.consentStore.reset();
}
