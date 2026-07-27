import { ProfileMode } from './profile';

export interface ConsentRecord {
  id: string;
  userId: string;
  profileMode: ProfileMode;
  researchDataConsent: boolean; // anonymized conversation data for research
  consentedAt: string;
  updatedAt: string;
}

export interface ConsentState {
  profileMode: ProfileMode | null;
  researchDataConsent: boolean;
  hasConsented: boolean;
}
