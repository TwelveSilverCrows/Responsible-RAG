import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useProfileStore } from '@/stores/profileStore';
import { useConsentStore } from '@/stores/consentStore';
import { profileSchema, type ProfileFormData } from '@/lib/schemas/profile.schema';
import type { DisabilityType } from '@/types/profile';

export function useProfileFormLogic() {
  const profileStore = useProfileStore();
  const consentStore = useConsentStore();

  const [genderOther, setGenderOther] = useState('');
  const [genderOtherSelected, setGenderOtherSelected] = useState(false);

  const form = useForm<ProfileFormData>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      preferredName: profileStore.profile?.preferredName ?? '',
      ageRange: profileStore.profile?.ageRange ?? undefined,
      genderIdentity: profileStore.profile?.genderIdentity ?? [],
      pronouns: profileStore.profile?.pronouns ?? '',
      primaryLanguage: profileStore.profile?.primaryLanguage ?? '',
      disability: profileStore.profile?.disability ?? [],
      immigrationStatus: profileStore.profile?.immigrationStatus ?? undefined,
      indigenousIdentity: profileStore.profile?.indigenousIdentity ?? undefined,
      educationLevel: profileStore.profile?.educationLevel ?? undefined,
      literacyComfortAI: profileStore.profile?.literacyComfortAI ?? 3,
    },
    mode: 'onTouched',
  });

  const { control, handleSubmit, trigger, formState, watch, setValue } = form;

  const getEffectiveGenderIdentity = (): string[] => {
    const current = watch('genderIdentity') ?? [];
    const filtered = current.filter((g) => g !== 'Other');
    if (genderOtherSelected && genderOther.trim()) {
      return [...filtered, genderOther.trim()];
    }
    return filtered;
  };

  const handleGenderCheckbox = (value: string, checked: boolean) => {
    const current = watch('genderIdentity') ?? [];
    if (checked) {
      setValue('genderIdentity', [...current, value], { shouldDirty: true });
    } else {
      setValue(
        'genderIdentity',
        current.filter((g) => g !== value),
        { shouldDirty: true }
      );
    }
  };

  const handleDisabilityCheckbox = (value: DisabilityType, checked: boolean) => {
    const current = watch('disability') ?? [];
    if (checked) {
      setValue('disability', [...current, value], { shouldDirty: true });
    } else {
      setValue(
        'disability',
        current.filter((d) => d !== value),
        { shouldDirty: true }
      );
    }
  };

  const submitProfile = (data: ProfileFormData) => {
    const genderIdentity = getEffectiveGenderIdentity();
    const now = new Date().toISOString();
    const existing = profileStore.profile;

    profileStore.setProfile({
      id: existing?.id ?? crypto.randomUUID(),
      userId: existing?.userId ?? 'local-user',
      preferredName: data.preferredName,
      ageRange: data.ageRange ?? null,
      genderIdentity,
      pronouns: data.pronouns ?? null,
      primaryLanguage: data.primaryLanguage ?? null,
      disability: data.disability ?? [],
      immigrationStatus: data.immigrationStatus ?? null,
      indigenousIdentity: data.indigenousIdentity ?? null,
      educationLevel: data.educationLevel ?? null,
      literacyComfortAI: data.literacyComfortAI ?? 3,
      profileMode: 'full',
      createdAt: existing?.createdAt ?? now,
      updatedAt: now,
    });

    consentStore.setProfileMode('full');
    consentStore.setHasConsented(true);
  };

  return {
    form,
    control,
    errors: formState.errors,
    isDirty: formState.isDirty,
    watch,
    setValue,
    trigger,
    handleSubmit,
    genderOther,
    genderOtherSelected,
    setGenderOther,
    setGenderOtherSelected,
    handleGenderCheckbox,
    handleDisabilityCheckbox,
    submitProfile,
  };
}

export type ProfileFormLogic = ReturnType<typeof useProfileFormLogic>;
