import { Controller, type Control, type UseFormWatch, type UseFormSetValue } from 'react-hook-form';
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
import { Separator } from '@/components/ui/separator';
import { SensitiveFieldGroup } from '@/components/profile/SensitiveFieldGroup';
import type { ProfileFormData } from '@/lib/schemas/profile.schema';
import { GENDER_OPTIONS, INDIGENOUS_OPTIONS, IMMIGRATION_OPTIONS } from '@/types/profile';

interface IdentityFieldsProps {
  control: Control<ProfileFormData>;
  watch: UseFormWatch<ProfileFormData>;
  setValue: UseFormSetValue<ProfileFormData>;
  genderOther: string;
  genderOtherSelected: boolean;
  setGenderOther: (value: string) => void;
  setGenderOtherSelected: (value: boolean) => void;
  handleGenderCheckbox: (value: string, checked: boolean) => void;
}

export function IdentityFields({
  control,
  watch,
  setValue,
  genderOther,
  genderOtherSelected,
  setGenderOther,
  setGenderOtherSelected,
  handleGenderCheckbox,
}: IdentityFieldsProps) {
  return (
    <>
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
                onCheckedChange={(checked) => handleGenderCheckbox(opt.value, checked === true)}
              />
              <Label htmlFor={`gender-${opt.value}`} className="text-sm font-normal cursor-pointer">
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
                  current.filter((g) => !GENDER_OPTIONS.some((o) => o.value === g)),
                  { shouldDirty: true }
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
            <Select value={field.value ?? ''} onValueChange={field.onChange}>
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
          Immigration status can affect access to services and information. This is used only to
          improve the relevance of responses you receive.
        </p>
        <Controller
          name="immigrationStatus"
          control={control}
          render={({ field }) => (
            <Select value={field.value ?? ''} onValueChange={field.onChange}>
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
    </>
  );
}
