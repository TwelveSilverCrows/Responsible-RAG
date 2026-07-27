'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronLeft, ChevronRight, Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { BasicInfoFields } from '@/components/profile/fields/BasicInfoFields';
import { IdentityFields } from '@/components/profile/fields/IdentityFields';
import { AccessibilityFields } from '@/components/profile/fields/AccessibilityFields';
import { useProfileFormLogic } from '@/hooks/useProfileFormLogic';
import type { ProfileFormData } from '@/lib/schemas/profile.schema';

interface FullProfileFormProps {
  onComplete: (complete: boolean) => void;
}

type SubStep = 1 | 2 | 3;

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
  const {
    control,
    errors,
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
  } = useProfileFormLogic();

  const [subStep, setSubStep] = useState<SubStep>(1);
  const [direction, setDirection] = useState(1);

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
    submitProfile(data);
    onComplete(true);
  };

  return (
    <div className="space-y-6">
      <div className="text-center space-y-2">
        <h2 className="font-display text-2xl sm:text-3xl font-semibold tracking-tight text-foreground">
          Tell us about yourself
        </h2>
        <p className="text-muted-foreground text-sm">
          This helps us tailor responses to your needs. Only your preferred name is required —
          everything else is optional.
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
              <div className={cn('w-8 h-0.5', subStep > step ? 'bg-primary/30' : 'bg-muted')} />
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

              <BasicInfoFields control={control} errors={errors} />

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

              <IdentityFields
                control={control}
                watch={watch}
                setValue={setValue}
                genderOther={genderOther}
                genderOtherSelected={genderOtherSelected}
                setGenderOther={setGenderOther}
                setGenderOtherSelected={setGenderOtherSelected}
                handleGenderCheckbox={handleGenderCheckbox}
              />

              <div className="flex justify-between pt-2">
                <Button type="button" variant="ghost" onClick={goSubBack} className="gap-1">
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
              <h3 className="font-display text-lg font-semibold">Accessibility</h3>

              <AccessibilityFields control={control} watch={watch} handleDisabilityCheckbox={handleDisabilityCheckbox} />

              <div className="flex justify-between pt-2">
                <Button type="button" variant="ghost" onClick={goSubBack} className="gap-1">
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
