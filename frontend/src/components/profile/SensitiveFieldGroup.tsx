'use client';

import { useState } from 'react';
import { HelpCircle, ChevronDown } from 'lucide-react';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { Label } from '@/components/ui/label';
import { cn } from '@/lib/utils';

interface SensitiveFieldGroupProps {
  label: string;
  description: string;
  children: React.ReactNode;
  hasPreferNotToSay?: boolean;
  htmlFor?: string;
}

export function SensitiveFieldGroup({
  label,
  description,
  children,
  hasPreferNotToSay = true,
  htmlFor,
}: SensitiveFieldGroupProps) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        {htmlFor ? (
          <Label htmlFor={htmlFor} className="text-sm font-medium">
            {label}
          </Label>
        ) : (
          <Label className="text-sm font-medium">{label}</Label>
        )}
        <Tooltip>
          <TooltipTrigger asChild>
            <button
              type="button"
              className="text-muted-foreground hover:text-foreground transition-colors"
              aria-label={`Why do we ask about ${label.toLowerCase()}?`}
            >
              <HelpCircle className="w-4 h-4" />
            </button>
          </TooltipTrigger>
          <TooltipContent side="right" className="max-w-xs">
            {description}
          </TooltipContent>
        </Tooltip>
      </div>

      <Collapsible open={isOpen} onOpenChange={setIsOpen}>
        <CollapsibleTrigger asChild>
          <button
            type="button"
            className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors group"
          >
            <ChevronDown
              className={cn(
                'w-3 h-3 transition-transform',
                isOpen && 'rotate-180'
              )}
            />
            <span className="group-hover:underline">
              Why do we ask this?
            </span>
          </button>
        </CollapsibleTrigger>
        <CollapsibleContent className="mt-2">
          <p className="text-xs text-muted-foreground bg-muted/50 rounded-md p-3 leading-relaxed">
            {description}
            {hasPreferNotToSay && (
              <>
                {' '}
                You can always choose{' '}
                <span className="font-medium italic">
                  &quot;Prefer not to say&quot;
                </span>{' '}
                if you&apos;d rather not share.
              </>
            )}
          </p>
        </CollapsibleContent>
      </Collapsible>

      <div className="mt-2">{children}</div>
    </div>
  );
}
