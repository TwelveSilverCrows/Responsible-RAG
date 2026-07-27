'use client';

import { useState } from 'react';
import { Lock, UserCheck } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { useConsentStore } from '@/stores/consentStore';
import { getModeDescription } from '@/lib/utils/privacyHelpers';
import { Link } from 'react-router-dom';
import { cn } from '@/lib/utils';

interface ProfileModeBadgeProps {
  variant?: 'sidebar' | 'chat';
}

export function ProfileModeBadge({ variant = 'chat' }: ProfileModeBadgeProps) {
  const { profileMode } = useConsentStore();
  const [showInfo, setShowInfo] = useState(false);

  if (!profileMode) return null;

  const isGeneral = profileMode === 'general';

  if (variant === 'sidebar') {
    return (
      <>
        <button
          onClick={() => setShowInfo(true)}
          className={cn(
            'flex items-center gap-2 text-xs px-3 py-1.5 rounded-full transition-colors w-full',
            isGeneral
              ? 'bg-muted text-muted-foreground'
              : 'bg-primary/10 text-primary'
          )}
        >
          {isGeneral ? (
            <Lock className="w-3.5 h-3.5 flex-shrink-0" />
          ) : (
            <UserCheck className="w-3.5 h-3.5 flex-shrink-0" />
          )}
          <span className="truncate">
            {isGeneral ? 'General mode' : 'Personalized'}
          </span>
        </button>
        <ModeInfoDialog open={showInfo} onOpenChange={setShowInfo} profileMode={profileMode} />
      </>
    );
  }

  return (
    <>
      <div className="flex items-center gap-2 px-4 py-2 border-b bg-muted/30">
        <Badge
          variant="outline"
          className={cn(
            'cursor-pointer transition-colors gap-1',
            isGeneral
              ? 'border-muted-foreground/30 text-muted-foreground'
              : 'border-primary/30 text-primary'
          )}
          onClick={() => setShowInfo(true)}
        >
          {isGeneral ? (
            <Lock className="w-3 h-3" />
          ) : (
            <UserCheck className="w-3 h-3" />
          )}
          {isGeneral ? 'General mode — no personal data stored' : 'Personalized — adapting to your profile'}
        </Badge>
      </div>
      <ModeInfoDialog open={showInfo} onOpenChange={setShowInfo} profileMode={profileMode} />
    </>
  );
}

function ModeInfoDialog({
  open,
  onOpenChange,
  profileMode,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  profileMode: 'full' | 'general';
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>
            {profileMode === 'full' ? 'Full Profile Mode' : 'General Mode'}
          </DialogTitle>
          <DialogDescription>{getModeDescription(profileMode)}</DialogDescription>
        </DialogHeader>
        <div className="space-y-3 text-sm text-muted-foreground">
          {profileMode === 'full' ? (
            <p>
              Your profile information is used to personalize AI responses to your accessibility
              needs, language preferences, and communication style. You can edit or delete your
              profile at any time from your settings.
            </p>
          ) : (
            <p>
              No personal information is stored about you. The AI will provide general responses
              without adaptation. After each conversation, you may be asked optional feedback
              questions to help improve the system.
            </p>
          )}
        </div>
        <div className="flex justify-end">
          <Button variant="outline" asChild>
            <Link to="/settings">Privacy Settings</Link>
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
