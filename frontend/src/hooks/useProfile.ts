'use client';

import { useProfileStore } from '@/stores/profileStore';
import { useConsentStore } from '@/stores/consentStore';

export function useProfile() {
  const profileStore = useProfileStore();
  const consentStore = useConsentStore();

  return {
    ...profileStore,
    profileMode: consentStore.profileMode,
    hasConsented: consentStore.hasConsented,
    isFullProfile: consentStore.profileMode === 'full',
    isGeneralMode: consentStore.profileMode === 'general',
  };
}
