'use client';

import { useState, useEffect } from 'react';
import { Save, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
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
import { BasicInfoFields } from '@/components/profile/fields/BasicInfoFields';
import { IdentityFields } from '@/components/profile/fields/IdentityFields';
import { AccessibilityFields } from '@/components/profile/fields/AccessibilityFields';
import { useProfileFormLogic } from '@/hooks/useProfileFormLogic';
import type { ProfileFormData } from '@/lib/schemas/profile.schema';

interface ProfileFormProps {
  onSave: () => void;
  onCancel: () => void;
}

export function ProfileForm({ onSave, onCancel }: ProfileFormProps) {
  const {
    control,
    errors,
    isDirty,
    watch,
    setValue,
    handleSubmit,
    genderOther,
    genderOtherSelected,
    setGenderOther,
    setGenderOtherSelected,
    handleGenderCheckbox,
    handleDisabilityCheckbox,
    submitProfile,
  } = useProfileFormLogic();

  const [showCancelDialog, setShowCancelDialog] = useState(false);

  // Track if form has unsaved edits
  const [hasEdited, setHasEdited] = useState(false);
  const watchedValues = watch();

  useEffect(() => {
    if (isDirty) {
      setHasEdited(true);
    }
  }, [isDirty, watchedValues]);

  const onSubmit = (data: ProfileFormData) => {
    submitProfile(data);
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
          <h3 className="font-display text-lg font-semibold text-foreground">Basic Info</h3>
          <BasicInfoFields control={control} errors={errors} />
        </section>

        <Separator />

        {/* ── Identity ────────────────────────────── */}
        <section className="space-y-6">
          <h3 className="font-display text-lg font-semibold text-foreground">Identity</h3>
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
        </section>

        <Separator />

        {/* ── Accessibility ───────────────────────── */}
        <section className="space-y-6">
          <h3 className="font-display text-lg font-semibold text-foreground">Accessibility</h3>
          <AccessibilityFields control={control} watch={watch} handleDisabilityCheckbox={handleDisabilityCheckbox} />
        </section>

        <Separator />

        {/* ── Action Buttons ───────────────────────── */}
        <div className="flex items-center justify-end gap-3 pt-2">
          <Button type="button" variant="outline" onClick={handleCancel} className="gap-1.5">
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
              You have unsaved edits to your profile. If you leave now, your changes will be lost.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Keep editing</AlertDialogCancel>
            <AlertDialogAction onClick={confirmCancel}>Discard changes</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
