import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { UserProfile, ProfileMode } from '@/types/profile';

interface ProfileStore {
  profile: UserProfile | null;
  isLoading: boolean;
  setProfile: (profile: UserProfile | null) => void;
  setLoading: (loading: boolean) => void;
  updateProfileMode: (mode: ProfileMode) => void;
  reset: () => void;
}

export const useProfileStore = create<ProfileStore>()(
  persist(
    (set) => ({
      profile: null,
      isLoading: false,
      setProfile: (profile) => set({ profile }),
      setLoading: (isLoading) => set({ isLoading }),
      updateProfileMode: (mode) =>
        set((state) => ({
          profile: state.profile ? { ...state.profile, profileMode: mode } : null,
        })),
      reset: () => set({ profile: null, isLoading: false }),
    }),
    { name: 'profile-store' }
  )
);
