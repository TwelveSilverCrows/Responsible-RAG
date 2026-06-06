'use client';

import { useState, useEffect } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Save, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Separator } from '@/components/ui/separator';
import { Textarea } from '@/components/ui/textarea';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { SensitiveFieldGroup } from '@/components/profile/SensitiveFieldGroup';
import { useProfileStore } from '@/stores/profileStore';
import { useConsentStore } from '@/stores/consentStore';
import { profileSchema, type ProfileFormData } from '@/lib/schemas/profile.schema';
import {
  AGE_RANGE_OPTIONS,
  LANGUAGE_OPTIONS,
  EDUCATION_OPTIONS,
  INDIGENOUS_OPTIONS,
  IMMIGRATION_OPTIONS,
  DISABILITY_OPTIONS,
  type DisabilityType,
} from '@/types/profile';

interface ProfileFormProps {
  onSave: () => void;
  onCancel: () => void;
}

const GENDER_OPTIONS: { value: string; label: string }[] = [
  { value: 'Man', label: 'Man' },
  { value: 'Woman', label: 'Woman' },
  { value: 'Non-binary', label: 'Non-binary' },
  { value: 'Genderqueer', label: 'Genderqueer' },
  { value: 'Two-Spirit', label: 'Two-Spirit' },
  { value: 'Prefer not to say', label: 'Prefer not to say' },
];

const COMFORT_LABELS: Record<number, string> = {
  1: 'Not comfortable',
  2: 'Slightly comfortable',
  3: 'Somewhat comfortable',
  4: 'Comfortable',
  5: 'Very comfortable',
};

export function ProfileForm({ onSave, onCancel }: ProfileFormProps) {
  const profileStore = useProfileStore();
  const consentStore = useConsentStore();

  const [genderOther, setGenderOther] = useState('');
  const [genderOtherSelected, setGenderOtherSelected] = useState(false);
  const [showCancelDialog, setShowCancelDialog] = useState(false);

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

  const {
    control,
    handleSubmit,
    formState: { errors, isDirty },
    watch,
    setValue,
  } = form;

  // Track if form has unsaved edits
  const [hasEdited, setHasEdited] = useState(false);
  const watchedValues = watch();

  useEffect(() => {
    if (isDirty) {
      setHasEdited(true);
    }
  }, [isDirty, watchedValues]);

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

  const onSubmit = (data: ProfileFormData) => {
    const genderIdentity = getEffectiveGenderIdentity();
    const now = new Date().toISOString();
    const userId = profileStore.profile?.userId ?? 'local-user';

    profileStore.setProfile({
      id: profileStore.profile?.id ?? crypto.randomUUID(),
      userId,
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
      createdAt: profileStore.profile?.createdAt ?? now,
      updatedAt: now,
    });

    consentStore.setProfileMode('full');
    consentStore.setHasConsented(true);
    onSave();
  };

  const handleCancel = () => {
    if (hasEdited) {
      setShowCancelDialog(true);
    } else {
      onCancel();
    }
  };

  const confirmCancel = () => {
    setShowCancelDialog(false);
    onCancel();
  };

  return (
    <>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-8">
        {/* ── Basic Info ──────────────────────────── */}
        <section className="space-y-5">
          <h3 className="font-display text-lg font-semibold text-foreground">
            Basic Info
          </h3>

          {/* Preferred name */}
          <div className="space-y-2">
            <Label htmlFor="preferredName">
              Preferred name <span className="text-destructive">*</span>
            </Label>
            <Controller
              name="preferredName"
              control={control}
              render={({ field }) => (
                <Input
                  {...field}
                  id="preferredName"
                  placeholder="What should we call you?"
                  aria-invalid={!!errors.preferredName}
                  aria-describedby={
                    errors.preferredName ? 'preferredName-error' : undefined
                  }
                />
              )}
            />
            {errors.preferredName && (
              <p id="preferredName-error" className="text-sm text-destructive">
                {errors.preferredName.message}
              </p>
            )}
          </div>

          {/* Age range */}
          <div className="space-y-2">
            <Label htmlFor="ageRange">Age range</Label>
            <Controller
              name="ageRange"
              control={control}
              render={({ field }) => (
                <Select
                  value={field.value ?? ''}
                  onValueChange={(val) => field.onChange(val)}
                >
                  <SelectTrigger id="ageRange" className="w-full">
                    <SelectValue placeholder="Select age range" />
                  </SelectTrigger>
                  <SelectContent>
                    {AGE_RANGE_OPTIONS.map((opt) => (
                      <SelectItem key={opt.value} value={opt.value}>
                        {opt.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            />
          </div>

          {/* Primary language */}
          <div className="space-y-2">
            <Label htmlFor="primaryLanguage">Primary language</Label>
            <Controller
              name="primaryLanguage"
              control={control}
              render={({ field }) => (
                <Select
                  value={field.value ?? ''}
                  onValueChange={(val) => field.onChange(val)}
                >
                  <SelectTrigger id="primaryLanguage" className="w-full">
                    <SelectValue placeholder="Select language" />
                  </SelectTrigger>
                  <SelectContent>
                    {LANGUAGE_OPTIONS.map((lang) => (
                      <SelectItem key={lang} value={lang}>
                        {lang}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            />
          </div>

          {/* Education level */}
          <div className="space-y-2">
            <Label htmlFor="educationLevel">Education level</Label>
            <Controller
              name="educationLevel"
              control={control}
              render={({ field }) => (
                <Select
                  value={field.value ?? ''}
                  onValueChange={(val) => field.onChange(val)}
                >
                  <SelectTrigger id="educationLevel" className="w-full">
                    <SelectValue placeholder="Select education level" />
                  </SelectTrigger>
                  <SelectContent>
                    {EDUCATION_OPTIONS.map((opt) => (
                      <SelectItem key={opt.value} value={opt.value}>
                        {opt.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            />
          </div>
        </section>

        <Separator />

        {/* ── Identity ────────────────────────────── */}
        <section className="space-y-6">
          <h3 className="font-display text-lg font-semibold text-foreground">
            Identity
          </h3>

          {/* Gender identity */}
          <SensitiveFieldGroup
            label="Gender identity"
            description="This helps us understand and serve diverse communities. Your response is optional and does not affect the quality of responses you receive."
            hasPreferNotToSay
          >
            <div className="grid grid-cols-2 gap-2">
              {GENDER_OPTIONS.map((opt) => (
                <div key={opt.value} className="flex items-center gap-2">
                  <Checkbox
                    id={`gender-${opt.value}`}
                    checked={(watch('genderIdentity') ?? []).includes(opt.value)}
                    onCheckedChange={(checked) =>
                      handleGenderCheckbox(opt.value, checked === true)
                    }
                  />
                  <Label
                    htmlFor={`gender-${opt.value}`}
                    className="text-sm font-normal cursor-pointer"
                  >
                    {opt.label}
                  </Label>
                </div>
              ))}
            </div>
            <div className="flex items-center gap-2 mt-2">
              <Checkbox
                id="gender-other-toggle"
                checked={genderOtherSelected}
                onCheckedChange={(checked) => {
                  setGenderOtherSelected(checked === true);
                  if (!checked) {
                    setGenderOther('');
                    const current = watch('genderIdentity') ?? [];
                    setValue(
                      'genderIdentity',
                      current.filter(
                        (g) => !GENDER_OPTIONS.some((o) => o.value === g)
                      ),
                      { shouldDirty: true }
                    );
                  }
                }}
              />
              <Label
                htmlFor="gender-other-toggle"
                className="text-sm font-normal cursor-pointer"
              >
                Other
              </Label>
            </div>
            {genderOtherSelected && (
              <Input
                value={genderOther}
                onChange={(e) => setGenderOther(e.target.value)}
                placeholder="Specify your gender identity"
                className="max-w-xs mt-2"
                aria-label="Specify your gender identity"
              />
            )}
          </SensitiveFieldGroup>

          <Separator />

          {/* Pronouns */}
          <div className="space-y-2">
            <Label htmlFor="pronouns">Pronouns</Label>
            <Controller
              name="pronouns"
              control={control}
              render={({ field }) => (
                <Input
                  {...field}
                  id="pronouns"
                  value={field.value ?? ''}
                  placeholder="e.g., she/her, they/them"
                />
              )}
            />
          </div>

          <Separator />

          {/* Indigenous identity */}
          <SensitiveFieldGroup
            label="Indigenous identity"
            description="This information helps us understand and serve diverse communities. It is entirely optional and does not affect your access to any services."
            hasPreferNotToSay
            htmlFor="indigenousIdentity"
          >
            <Controller
              name="indigenousIdentity"
              control={control}
              render={({ field }) => (
                <Select
                  value={field.value ?? ''}
                  onValueChange={(val) => field.onChange(val)}
                >
                  <SelectTrigger id="indigenousIdentity" className="w-full">
                    <SelectValue placeholder="Select Indigenous identity" />
                  </SelectTrigger>
                  <SelectContent>
                    {INDIGENOUS_OPTIONS.map((opt) => (
                      <SelectItem key={opt.value} value={opt.value}>
                        {opt.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            />
          </SensitiveFieldGroup>

          <Separator />

          {/* Immigration / residency status */}
          <SensitiveFieldGroup
            label="Immigration / residency status"
            description="We ask this because immigration status can affect access to services and information. This data is used only to improve response relevance. It is entirely optional."
            hasPreferNotToSay
            htmlFor="immigrationStatus"
          >
            <p className="text-xs text-muted-foreground mb-2">
              Immigration status can affect access to services and information.
              This is used only to improve the relevance of responses you
              receive.
            </p>
            <Controller
              name="immigrationStatus"
              control={control}
              render={({ field }) => (
                <Select
                  value={field.value ?? ''}
                  onValueChange={(val) => field.onChange(val)}
                >
                  <SelectTrigger id="immigrationStatus" className="w-full">
                    <SelectValue placeholder="Select immigration status" />
                  </SelectTrigger>
                  <SelectContent>
                    {IMMIGRATION_OPTIONS.map((opt) => (
                      <SelectItem key={opt.value} value={opt.value}>
                        {opt.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            />
          </SensitiveFieldGroup>
        </section>

        <Separator />

        {/* ── Accessibility ───────────────────────── */}
        <section className="space-y-6">
          <h3 className="font-display text-lg font-semibold text-foreground">
            Accessibility
          </h3>

          {/* Disability multi-select */}
          <SensitiveFieldGroup
            label="Disability or accessibility needs"
            description="Understanding your accessibility needs helps us provide better-formatted responses and accommodations. This is entirely optional."
            hasPreferNotToSay
          >
            <div className="space-y-3 max-h-64 overflow-y-auto pr-1">
              {DISABILITY_OPTIONS.map((opt) => (
                <div key={opt.value} className="flex items-start gap-3">
                  <Checkbox
                    id={`disability-${opt.value}`}
                    checked={(watch('disability') ?? []).includes(opt.value)}
                    onCheckedChange={(checked) =>
                      handleDisabilityCheckbox(opt.value, checked === true)
                    }
                    className="mt-0.5"
                  />
                  <div className="flex-1">
                    <Label
                      htmlFor={`disability-${opt.value}`}
                      className="text-sm font-normal cursor-pointer"
                    >
                      {opt.label}
                    </Label>
                    {opt.description && (
                      <p className="text-xs text-muted-foreground mt-0.5">
                        {opt.description}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </SensitiveFieldGroup>

          <Separator />

          {/* Literacy comfort with AI */}
          <SensitiveFieldGroup
            label="Comfort level with AI"
            description="This helps us calibrate how we present information and explanations. There are no wrong answers — we just want to make the experience comfortable for you."
            hasPreferNotToSay={false}
          >
            <p className="text-xs text-muted-foreground mb-3">
              How comfortable are you interacting with AI systems?
            </p>
            <Controller
              name="literacyComfortAI"
              control={control}
              render={({ field }) => (
                <RadioGroup
                  value={String(field.value ?? 3)}
                  onValueChange={(val) => field.onChange(Number(val))}
                  className="space-y-2"
                >
                  {([1, 2, 3, 4, 5] as const).map((num) => (
                    <div key={num} className="flex items-center gap-3">
                      <RadioGroupItem
                        value={String(num)}
                        id={`comfort-${num}`}
                      />
                      <Label
                        htmlFor={`comfort-${num}`}
                        className="text-sm font-normal cursor-pointer flex items-center gap-2"
                      >
                        <span className="w-4 text-center font-medium text-muted-foreground">
                          {num}
                        </span>
                        <span>{COMFORT_LABELS[num]}</span>
                      </Label>
                    </div>
                  ))}
                </RadioGroup>
              )}
            />
          </SensitiveFieldGroup>
        </section>

        <Separator />

        {/* ── Action Buttons ───────────────────────── */}
        <div className="flex items-center justify-end gap-3 pt-2">
          <Button
            type="button"
            variant="outline"
            onClick={handleCancel}
            className="gap-1.5"
          >
            <X className="w-4 h-4" />
            Cancel
          </Button>
          <Button type="submit" className="gap-1.5">
            <Save className="w-4 h-4" />
            Save changes
          </Button>
        </div>
      </form>

      {/* Cancel confirmation dialog */}
      <AlertDialog open={showCancelDialog} onOpenChange={setShowCancelDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Discard changes?</AlertDialogTitle>
            <AlertDialogDescription>
              You have unsaved edits to your profile. If you leave now, your
              changes will be lost.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Keep editing</AlertDialogCancel>
            <AlertDialogAction onClick={confirmCancel}>
              Discard changes
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
