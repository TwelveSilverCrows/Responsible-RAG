'use client';

import { useConsentStore } from '@/stores/consentStore';

export function useConsent() {
  const store = useConsentStore();
  return {
    ...store,
    isFullProfile: store.profileMode === 'full',
    isGeneralMode: store.profileMode === 'general',
    canProceed: store.profileMode !== null,
  };
}
