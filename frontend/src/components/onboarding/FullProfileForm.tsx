'use client';

import { useState } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ChevronLeft,
  ChevronRight,
  HelpCircle,
  Check,
} from 'lucide-react';
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
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { Separator } from '@/components/ui/separator';
import { cn } from '@/lib/utils';
import { useConsentStore } from '@/stores/consentStore';
import { useProfileStore } from '@/stores/profileStore';
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

interface FullProfileFormProps {
  onComplete: (complete: boolean) => void;
}

type SubStep = 1 | 2 | 3;

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

const subStepVariants = {
  enter: (direction: number) => ({
    x: direction > 0 ? 200 : -200,
    opacity: 0,
  }),
  center: { x: 0, opacity: 1 },
  exit: (direction: number) => ({
    x: direction < 0 ? 200 : -200,
    opacity: 0,
  }),
};

export function FullProfileForm({ onComplete }: FullProfileFormProps) {
  const consentStore = useConsentStore();
  const profileStore = useProfileStore();

  const [subStep, setSubStep] = useState<SubStep>(1);
  const [direction, setDirection] = useState(1);
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

  const { control, handleSubmit, trigger, formState: { errors }, watch, setValue } = form;

  // Build the effective gender identity array (checkboxes + other text)
  const getEffectiveGenderIdentity = (): string[] => {
    const current = watch('genderIdentity') ?? [];
    const filtered = current.filter((g) => g !== 'Other');
    if (genderOtherSelected && genderOther.trim()) {
      return [...filtered, genderOther.trim()];
    }
    return filtered;
  };

  const goSubNext = async () => {
    let fieldsToValidate: string[] = [];
    if (subStep === 1) {
      fieldsToValidate = ['preferredName'];
    }
    // Steps 2 and 3 have no required fields (besides what's in step 1)

    const valid = await trigger(fieldsToValidate as never[]);
    if (!valid) return;

    if (subStep < 3) {
      setDirection(1);
      setSubStep((s) => Math.min(s + 1, 3) as SubStep);
    }
  };

  const goSubBack = () => {
    if (subStep > 1) {
      setDirection(-1);
      setSubStep((s) => Math.max(s - 1, 1) as SubStep);
    }
  };

  const onSubmit = (data: ProfileFormData) => {
    // Build effective gender identity
    const genderIdentity = getEffectiveGenderIdentity();

    const now = new Date().toISOString();
    const userId = 'local-user';

    profileStore.setProfile({
      id: crypto.randomUUID(),
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
      createdAt: now,
      updatedAt: now,
    });

    consentStore.setHasConsented(true);
    consentStore.setProfileMode('full');
    onComplete(true);
  };

  const handleGenderCheckbox = (value: string, checked: boolean) => {
    const current = watch('genderIdentity') ?? [];
    if (checked) {
      setValue('genderIdentity', [...current, value]);
    } else {
      setValue('genderIdentity', current.filter((g) => g !== value));
    }
  };

  const handleDisabilityCheckbox = (value: DisabilityType, checked: boolean) => {
    const current = watch('disability') ?? [];
    if (checked) {
      setValue('disability', [...current, value]);
    } else {
      setValue('disability', current.filter((d) => d !== value));
    }
  };

  return (
    <div className="space-y-6">
      <div className="text-center space-y-2">
        <h2 className="font-display text-2xl sm:text-3xl font-semibold tracking-tight text-foreground">
          Tell us about yourself
        </h2>
        <p className="text-muted-foreground text-sm">
          This helps us tailor responses to your needs. Only your preferred name
          is required — everything else is optional.
        </p>
      </div>

      {/* Sub-step indicator */}
      <div className="flex items-center justify-center gap-3">
        {([1, 2, 3] as SubStep[]).map((step) => (
          <div key={step} className="flex items-center gap-2">
            <div
              className={cn(
                'w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium transition-colors',
                subStep === step && 'bg-primary text-primary-foreground',
                subStep > step && 'bg-primary/20 text-primary',
                subStep < step && 'bg-muted text-muted-foreground'
              )}
              aria-current={subStep === step ? 'step' : undefined}
            >
              {subStep > step ? <Check className="w-4 h-4" /> : step}
            </div>
            {step < 3 && (
              <div
                className={cn(
                  'w-8 h-0.5',
                  subStep > step ? 'bg-primary/30' : 'bg-muted'
                )}
              />
            )}
          </div>
        ))}
      </div>

      <form onSubmit={handleSubmit(onSubmit)}>
        <AnimatePresence mode="wait" custom={direction}>
          {/* ── Sub-step 1: Basic Info ──────────────────────────── */}
          {subStep === 1 && (
            <motion.div
              key="sub1"
              custom={direction}
              variants={subStepVariants}
              initial="enter"
              animate="center"
              exit="exit"
              transition={{ duration: 0.25, ease: 'easeInOut' }}
              className="space-y-5"
            >
              <h3 className="font-display text-lg font-semibold">Basic Info</h3>

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
                      onValueChange={field.onChange}
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
                      onValueChange={field.onChange}
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
                      onValueChange={field.onChange}
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

              {/* Sub-step nav */}
              <div className="flex justify-end pt-2">
                <Button type="button" onClick={goSubNext} className="gap-1">
                  Continue
                  <ChevronRight className="w-4 h-4" />
                </Button>
              </div>
            </motion.div>
          )}

          {/* ── Sub-step 2: Identity ────────────────────────────── */}
          {subStep === 2 && (
            <motion.div
              key="sub2"
              custom={direction}
              variants={subStepVariants}
              initial="enter"
              animate="center"
              exit="exit"
              transition={{ duration: 0.25, ease: 'easeInOut' }}
              className="space-y-6"
            >
              <h3 className="font-display text-lg font-semibold">Identity</h3>

              {/* Gender identity */}
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <Label>Gender identity</Label>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <button
                        type="button"
                        className="text-muted-foreground hover:text-foreground transition-colors"
                        aria-label="Why do we ask about gender identity?"
                      >
                        <HelpCircle className="w-4 h-4" />
                      </button>
                    </TooltipTrigger>
                    <TooltipContent side="right" className="max-w-xs">
                      This helps us understand and serve diverse communities.
                      It&apos;s entirely optional and you can choose &quot;Prefer not
                      to say.&quot;
                    </TooltipContent>
                  </Tooltip>
                </div>
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
                {/* Other text input */}
                <div className="flex items-center gap-2">
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
                          current.filter((g) => !GENDER_OPTIONS.some((o) => o.value === g))
                        );
                      }
                    }}
                  />
                  <Label htmlFor="gender-other-toggle" className="text-sm font-normal cursor-pointer">
                    Other
                  </Label>
                </div>
                {genderOtherSelected && (
                  <Input
                    value={genderOther}
                    onChange={(e) => setGenderOther(e.target.value)}
                    placeholder="Specify your gender identity"
                    className="max-w-xs"
                    aria-label="Specify your gender identity"
                  />
                )}
              </div>

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
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <Label htmlFor="indigenousIdentity">Indigenous identity</Label>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <button
                        type="button"
                        className="text-muted-foreground hover:text-foreground transition-colors"
                        aria-label="Why do we ask about Indigenous identity?"
                      >
                        <HelpCircle className="w-4 h-4" />
                      </button>
                    </TooltipTrigger>
                    <TooltipContent side="right" className="max-w-xs">
                      This information helps us understand and serve diverse
                      communities. It is entirely optional.
                    </TooltipContent>
                  </Tooltip>
                </div>
                <p className="text-xs text-muted-foreground">
                  This information helps us understand and serve diverse
                  communities. It is entirely optional.
                </p>
                <Controller
                  name="indigenousIdentity"
                  control={control}
                  render={({ field }) => (
                    <Select
                      value={field.value ?? ''}
                      onValueChange={field.onChange}
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
              </div>

              <Separator />

              {/* Immigration / residency status */}
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <Label htmlFor="immigrationStatus">
                    Immigration / residency status
                  </Label>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <button
                        type="button"
                        className="text-muted-foreground hover:text-foreground transition-colors"
                        aria-label="Why do we ask about immigration status?"
                      >
                        <HelpCircle className="w-4 h-4" />
                      </button>
                    </TooltipTrigger>
                    <TooltipContent side="right" className="max-w-xs">
                      We ask this because immigration status can affect access to
                      services and information. This data is used only to improve
                      response relevance.
                    </TooltipContent>
                  </Tooltip>
                </div>
                <p className="text-xs text-muted-foreground">
                  We ask this because immigration status can affect access to
                  services and information. This data is used only to improve
                  response relevance.
                </p>
                <Controller
                  name="immigrationStatus"
                  control={control}
                  render={({ field }) => (
                    <Select
                      value={field.value ?? ''}
                      onValueChange={field.onChange}
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
              </div>

              {/* Sub-step nav */}
              <div className="flex justify-between pt-2">
                <Button
                  type="button"
                  variant="ghost"
                  onClick={goSubBack}
                  className="gap-1"
                >
                  <ChevronLeft className="w-4 h-4" />
                  Back
                </Button>
                <Button type="button" onClick={goSubNext} className="gap-1">
                  Continue
                  <ChevronRight className="w-4 h-4" />
                </Button>
              </div>
            </motion.div>
          )}

          {/* ── Sub-step 3: Accessibility ───────────────────────── */}
          {subStep === 3 && (
            <motion.div
              key="sub3"
              custom={direction}
              variants={subStepVariants}
              initial="enter"
              animate="center"
              exit="exit"
              transition={{ duration: 0.25, ease: 'easeInOut' }}
              className="space-y-6"
            >
              <h3 className="font-display text-lg font-semibold">
                Accessibility
              </h3>

              {/* Disability multi-select */}
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <Label>Disability or accessibility needs</Label>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <button
                        type="button"
                        className="text-muted-foreground hover:text-foreground transition-colors"
                        aria-label="Why do we ask about disability?"
                      >
                        <HelpCircle className="w-4 h-4" />
                      </button>
                    </TooltipTrigger>
                    <TooltipContent side="right" className="max-w-xs">
                      Understanding your accessibility needs helps us provide
                      better-format responses and accommodations. This is
                      optional.
                    </TooltipContent>
                  </Tooltip>
                </div>
                <div className="space-y-3 max-h-64 overflow-y-auto custom-scrollbar pr-1">
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
              </div>

              <Separator />

              {/* Literacy comfort with AI */}
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <Label>Comfort level with AI</Label>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <button
                        type="button"
                        className="text-muted-foreground hover:text-foreground transition-colors"
                        aria-label="Why do we ask about AI comfort level?"
                      >
                        <HelpCircle className="w-4 h-4" />
                      </button>
                    </TooltipTrigger>
                    <TooltipContent side="right" className="max-w-xs">
                      This helps us calibrate how we present information and
                      explanations. There are no wrong answers.
                    </TooltipContent>
                  </Tooltip>
                </div>
                <p className="text-xs text-muted-foreground">
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
              </div>

              {/* Sub-step nav */}
              <div className="flex justify-between pt-2">
                <Button
                  type="button"
                  variant="ghost"
                  onClick={goSubBack}
                  className="gap-1"
                >
                  <ChevronLeft className="w-4 h-4" />
                  Back
                </Button>
                <Button type="submit" className="gap-1">
                  Complete setup
                  <Check className="w-4 h-4" />
                </Button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </form>
    </div>
  );
}
