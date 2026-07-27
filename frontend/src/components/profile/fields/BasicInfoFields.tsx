import { Controller, type Control, type FieldErrors } from 'react-hook-form';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import type { ProfileFormData } from '@/lib/schemas/profile.schema';
import { AGE_RANGE_OPTIONS, LANGUAGE_OPTIONS, EDUCATION_OPTIONS } from '@/types/profile';

interface BasicInfoFieldsProps {
  control: Control<ProfileFormData>;
  errors: FieldErrors<ProfileFormData>;
}

export function BasicInfoFields({ control, errors }: BasicInfoFieldsProps) {
  return (
    <>
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
              aria-describedby={errors.preferredName ? 'preferredName-error' : undefined}
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
            <Select value={field.value ?? ''} onValueChange={field.onChange}>
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
            <Select value={field.value ?? ''} onValueChange={field.onChange}>
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
            <Select value={field.value ?? ''} onValueChange={field.onChange}>
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
    </>
  );
}
