import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { ProfileMode } from '@/types/profile';

interface ConsentStore {
  profileMode: ProfileMode | null;
  researchDataConsent: boolean;
  hasConsented: boolean;
  setProfileMode: (mode: ProfileMode) => void;
  setResearchDataConsent: (consent: boolean) => void;
  setHasConsented: (consented: boolean) => void;
  reset: () => void;
}

export const useConsentStore = create<ConsentStore>()(
  persist(
    (set) => ({
      profileMode: null,
      researchDataConsent: false,
      hasConsented: false,
      setProfileMode: (mode) => set({ profileMode: mode }),
      setResearchDataConsent: (consent) => set({ researchDataConsent: consent }),
      setHasConsented: (consented) => set({ hasConsented: consented }),
      reset: () => set({ profileMode: null, researchDataConsent: false, hasConsented: false }),
    }),
    { name: 'consent-store' }
  )
);
