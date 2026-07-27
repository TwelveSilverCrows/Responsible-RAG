import { Controller, type Control, type UseFormWatch } from 'react-hook-form';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Separator } from '@/components/ui/separator';
import { SensitiveFieldGroup } from '@/components/profile/SensitiveFieldGroup';
import type { ProfileFormData } from '@/lib/schemas/profile.schema';
import { DISABILITY_OPTIONS, COMFORT_LABELS, type DisabilityType } from '@/types/profile';

interface AccessibilityFieldsProps {
  control: Control<ProfileFormData>;
  watch: UseFormWatch<ProfileFormData>;
  handleDisabilityCheckbox: (value: DisabilityType, checked: boolean) => void;
}

export function AccessibilityFields({ control, watch, handleDisabilityCheckbox }: AccessibilityFieldsProps) {
  return (
    <>
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
                onCheckedChange={(checked) => handleDisabilityCheckbox(opt.value, checked === true)}
                className="mt-0.5"
              />
              <div className="flex-1">
                <Label htmlFor={`disability-${opt.value}`} className="text-sm font-normal cursor-pointer">
                  {opt.label}
                </Label>
                {opt.description && (
                  <p className="text-xs text-muted-foreground mt-0.5">{opt.description}</p>
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
                  <RadioGroupItem value={String(num)} id={`comfort-${num}`} />
                  <Label
                    htmlFor={`comfort-${num}`}
                    className="text-sm font-normal cursor-pointer flex items-center gap-2"
                  >
                    <span className="w-4 text-center font-medium text-muted-foreground">{num}</span>
                    <span>{COMFORT_LABELS[num]}</span>
                  </Label>
                </div>
              ))}
            </RadioGroup>
          )}
        />
      </SensitiveFieldGroup>
    </>
  );
}
