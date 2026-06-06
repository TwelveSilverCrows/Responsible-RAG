'use client';

import { useState } from 'react';
import { Pencil, Eye, EyeOff, Shield } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { AppShell } from '@/components/layout/AppShell';
import { ProfileForm } from '@/components/profile/ProfileForm';
import { ConsentPanel } from '@/components/profile/ConsentPanel';
import { AuthGuard } from '@/components/AuthGuard';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { useProfileStore } from '@/stores/profileStore';
import { useConsentStore } from '@/stores/consentStore';
import {
  AGE_RANGE_OPTIONS,
  EDUCATION_OPTIONS,
  INDIGENOUS_OPTIONS,
  IMMIGRATION_OPTIONS,
  DISABILITY_OPTIONS,
  LANGUAGE_OPTIONS,
} from '@/types/profile';
import { cn } from '@/lib/utils';

const COMFORT_LABELS: Record<number, string> = {
  1: 'Not comfortable',
  2: 'Slightly comfortable',
  3: 'Somewhat comfortable',
  4: 'Comfortable',
  5: 'Very comfortable',
};

function getOptionLabel(
  options: readonly { value: string; label: string }[],
  value: string | null | undefined
): string {
  if (!value) return 'Not specified';
  if (value === 'prefer_not_to_say') return 'Not specified';
  const opt = options.find((o) => o.value === value);
  return opt?.label ?? value;
}

export default function ProfilePage() {
  const { profile } = useProfileStore();
  const { profileMode } = useConsentStore();
  const [isEditing, setIsEditing] = useState(false);
  const [showIdentity, setShowIdentity] = useState(false);

  const isGeneralMode =
    profileMode === 'general' || profile?.profileMode === 'general';

  // General mode with no profile
  if (isGeneralMode && !profile) {
    return (
      <AuthGuard>
      <AppShell>
        <div className="max-w-2xl mx-auto px-4 py-8 sm:py-12">
          <div className="text-center space-y-4 py-12">
            <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mx-auto">
              <Shield className="w-8 h-8 text-muted-foreground" />
            </div>
            <h1 className="font-display text-2xl font-semibold text-foreground">
              General Mode
            </h1>
            <p className="text-muted-foreground max-w-md mx-auto">
              You&apos;re in General mode. No profile data is stored. If
              you&apos;d like personalized responses, you can switch to Full
              Profile mode from your{' '}
              <a
                href="/settings"
                className="text-primary hover:underline font-medium"
              >
                Privacy Settings
              </a>
              .
            </p>
          </div>
        </div>
      </AppShell>
      </AuthGuard>
    );
  }

  // Editing mode
  if (isEditing && profile) {
    return (
      <AuthGuard>
      <AppShell>
        <div className="max-w-2xl mx-auto px-4 py-8 sm:py-12">
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h1 className="font-display text-2xl font-semibold text-foreground">
                Edit Profile
              </h1>
            </div>
            <AnimatePresence mode="wait">
              <motion.div
                key="edit"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.2 }}
              >
                <ProfileForm
                  onSave={() => setIsEditing(false)}
                  onCancel={() => setIsEditing(false)}
                />
              </motion.div>
            </AnimatePresence>
          </div>
        </div>
      </AppShell>
      </AuthGuard>
    );
  }

  // Read mode with profile
  const initials = profile?.preferredName
    ? profile.preferredName
        .split(' ')
        .map((n) => n[0])
        .join('')
        .toUpperCase()
        .slice(0, 2)
    : 'U';

  return (
    <AuthGuard>
    <AppShell>
      <div className="max-w-2xl mx-auto px-4 py-8 sm:py-12">
        <div className="space-y-8">
          {/* Header with avatar and edit button */}
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-4">
              <Avatar className="w-16 h-16">
                <AvatarFallback className="bg-primary/10 text-primary text-xl font-display font-semibold">
                  {initials}
                </AvatarFallback>
              </Avatar>
              <div>
                <h1 className="font-display text-2xl font-semibold text-foreground">
                  {profile?.preferredName ?? 'User'}
                </h1>
                <Badge
                  variant="outline"
                  className={cn(
                    'mt-1',
                    profile?.profileMode === 'full'
                      ? 'border-primary/30 text-primary'
                      : 'border-muted-foreground/30 text-muted-foreground'
                  )}
                >
                  {profile?.profileMode === 'full'
                    ? 'Personalized'
                    : 'General'}{' '}
                  Mode
                </Badge>
              </div>
            </div>
            <Button
              variant="outline"
              className="gap-1.5"
              onClick={() => setIsEditing(true)}
            >
              <Pencil className="w-4 h-4" />
              Edit
            </Button>
          </div>

          <Separator />

          {/* Personal Info */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base font-display">
                Personal Information
              </CardTitle>
            </CardHeader>
            <CardContent>
              <dl className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-4">
                <div>
                  <dt className="text-xs text-muted-foreground font-medium">
                    Display name
                  </dt>
                  <dd className="text-sm mt-0.5">{profile?.preferredName}</dd>
                </div>
                <div>
                  <dt className="text-xs text-muted-foreground font-medium">
                    Age range
                  </dt>
                  <dd className="text-sm mt-0.5">
                    {getOptionLabel(AGE_RANGE_OPTIONS, profile?.ageRange)}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-muted-foreground font-medium">
                    Primary language
                  </dt>
                  <dd className="text-sm mt-0.5">
                    {profile?.primaryLanguage ?? 'Not specified'}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-muted-foreground font-medium">
                    Education level
                  </dt>
                  <dd className="text-sm mt-0.5">
                    {getOptionLabel(EDUCATION_OPTIONS, profile?.educationLevel)}
                  </dd>
                </div>
              </dl>
            </CardContent>
          </Card>

          {/* Accessibility Preferences */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base font-display">
                Accessibility Preferences
              </CardTitle>
            </CardHeader>
            <CardContent>
              <dl className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-4">
                <div>
                  <dt className="text-xs text-muted-foreground font-medium">
                    Accessibility needs
                  </dt>
                  <dd className="text-sm mt-0.5">
                    {profile?.disability && profile.disability.length > 0
                      ? profile.disability
                          .map((d) => {
                            if (d === 'prefer_not_to_say') return 'Not specified';
                            const opt = DISABILITY_OPTIONS.find(
                              (o) => o.value === d
                            );
                            return opt?.label ?? d;
                          })
                          .join(', ')
                      : 'Not specified'}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-muted-foreground font-medium">
                    AI comfort level
                  </dt>
                  <dd className="text-sm mt-0.5">
                    {profile?.literacyComfortAI
                      ? `${profile.literacyComfortAI}/5 — ${COMFORT_LABELS[profile.literacyComfortAI]}`
                      : 'Not specified'}
                  </dd>
                </div>
              </dl>
            </CardContent>
          </Card>

          {/* Identity Fields — behind toggle */}
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base font-display">
                  Identity Information
                </CardTitle>
                <Button
                  variant="ghost"
                  size="sm"
                  className="gap-1.5 text-muted-foreground"
                  onClick={() => setShowIdentity(!showIdentity)}
                >
                  {showIdentity ? (
                    <>
                      <EyeOff className="w-4 h-4" />
                      Hide
                    </>
                  ) : (
                    <>
                      <Eye className="w-4 h-4" />
                      Show identity fields
                    </>
                  )}
                </Button>
              </div>
            </CardHeader>
            {showIdentity && (
              <CardContent>
                <AnimatePresence>
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    transition={{ duration: 0.2 }}
                  >
                    <dl className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-4">
                      <div>
                        <dt className="text-xs text-muted-foreground font-medium">
                          Gender identity
                        </dt>
                        <dd className="text-sm mt-0.5">
                          {profile?.genderIdentity &&
                          profile.genderIdentity.length > 0
                            ? profile.genderIdentity
                                .map((g) =>
                                  g === 'Prefer not to say'
                                    ? 'Not specified'
                                    : g
                                )
                                .join(', ')
                            : 'Not specified'}
                        </dd>
                      </div>
                      <div>
                        <dt className="text-xs text-muted-foreground font-medium">
                          Pronouns
                        </dt>
                        <dd className="text-sm mt-0.5">
                          {profile?.pronouns ?? 'Not specified'}
                        </dd>
                      </div>
                      <div>
                        <dt className="text-xs text-muted-foreground font-medium">
                          Indigenous identity
                        </dt>
                        <dd className="text-sm mt-0.5">
                          {getOptionLabel(
                            INDIGENOUS_OPTIONS,
                            profile?.indigenousIdentity
                          )}
                        </dd>
                      </div>
                      <div>
                        <dt className="text-xs text-muted-foreground font-medium">
                          Immigration status
                        </dt>
                        <dd className="text-sm mt-0.5">
                          {getOptionLabel(
                            IMMIGRATION_OPTIONS,
                            profile?.immigrationStatus
                          )}
                        </dd>
                      </div>
                    </dl>
                  </motion.div>
                </AnimatePresence>
              </CardContent>
            )}
          </Card>

          {/* Consent Panel */}
          <ConsentPanel />
        </div>
      </div>
    </AppShell>
    </AuthGuard>
  );
}
