'use client';

import { Shield, MessageSquare } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useConsentStore } from '@/stores/consentStore';
import { FullProfileForm } from './FullProfileForm';

interface ProfileModeSelectorProps {
  onComplete: (complete: boolean) => void;
}

export function ProfileModeSelector({ onComplete }: ProfileModeSelectorProps) {
  const consentStore = useConsentStore();

  // If general mode, show confirmation
  if (consentStore.profileMode === 'general') {
    return (
      <div className="space-y-6 text-center">
        <div className="flex justify-center">
          <div className="w-14 h-14 rounded-full bg-primary/10 flex items-center justify-center">
            <Shield className="w-7 h-7 text-primary" />
          </div>
        </div>
        <div className="space-y-2">
          <h2 className="font-display text-2xl sm:text-3xl font-semibold tracking-tight text-foreground">
            You&apos;re all set
          </h2>
          <p className="text-muted-foreground text-base max-w-md mx-auto">
            No personal data will be stored. You can start chatting right away.
          </p>
        </div>
        <Button
          size="lg"
          className="gap-2 mt-4"
          onClick={() => onComplete(true)}
        >
          <MessageSquare className="w-4 h-4" />
          Start chatting
        </Button>
      </div>
    );
  }

  // If full profile mode, show the form
  if (consentStore.profileMode === 'full') {
    return <FullProfileForm onComplete={onComplete} />;
  }

  // Fallback — shouldn't reach here normally
  return (
    <div className="text-center text-muted-foreground">
      <p>Please go back and select a privacy option first.</p>
    </div>
  );
}
