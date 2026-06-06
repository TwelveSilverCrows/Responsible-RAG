'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronLeft, ChevronRight, Shield } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { useConsentStore } from '@/stores/consentStore';
import { useAuthStore } from '@/hooks/useAuth';
import { ConsentStep } from './ConsentStep';
import { ProfileModeSelector } from './ProfileModeSelector';

type WizardStep = 'welcome' | 'consent' | 'profile';

const STEPS: { key: WizardStep; label: string }[] = [
  { key: 'welcome', label: 'Welcome' },
  { key: 'consent', label: 'Privacy' },
  { key: 'profile', label: 'Profile' },
];

const STEP_ORDER: WizardStep[] = ['welcome', 'consent', 'profile'];

const STORAGE_KEY = 'onboarding-step';

const slideVariants = {
  enter: (direction: number) => ({
    x: direction > 0 ? 300 : -300,
    opacity: 0,
  }),
  center: {
    x: 0,
    opacity: 1,
  },
  exit: (direction: number) => ({
    x: direction < 0 ? 300 : -300,
    opacity: 0,
  }),
};

function getInitialStep(): WizardStep {
  if (typeof window !== 'undefined') {
    try {
      const saved = sessionStorage.getItem(STORAGE_KEY);
      if (saved && STEP_ORDER.includes(saved as WizardStep)) {
        return saved as WizardStep;
      }
    } catch {
      // sessionStorage not available
    }
  }
  return 'welcome';
}

export function OnboardingWizard() {
  const router = useRouter();

  const [currentStep, setCurrentStep] = useState<WizardStep>(getInitialStep);
  const [direction, setDirection] = useState(1);
  const [consentComplete, setConsentComplete] = useState(false);
  const [profileComplete, setProfileComplete] = useState(false);
  // Persist step to sessionStorage when it changes
  useEffect(() => {
    try {
      sessionStorage.setItem(STORAGE_KEY, currentStep);
    } catch {
      // sessionStorage not available
    }
  }, [currentStep]);

  const stepIndex = STEP_ORDER.indexOf(currentStep);

  const canGoBack = stepIndex > 0;
  const canGoForward = useCallback(() => {
    if (currentStep === 'welcome') return true;
    if (currentStep === 'consent') return consentComplete;
    if (currentStep === 'profile') return profileComplete;
    return false;
  }, [currentStep, consentComplete, profileComplete]);

  const goNext = () => {
    if (!canGoForward()) return;
    const nextIndex = stepIndex + 1;
    if (nextIndex < STEP_ORDER.length) {
      setDirection(1);
      setCurrentStep(STEP_ORDER[nextIndex]);
    }
  };

  const goBack = () => {
    if (!canGoBack) return;
    setDirection(-1);
    setCurrentStep(STEP_ORDER[stepIndex - 1]);
  };

  const handleComplete = () => {
    try {
      sessionStorage.removeItem(STORAGE_KEY);
    } catch {
      // sessionStorage not available
    }
    // Mark onboarding as completed so root redirect works properly
    useAuthStore.getState().completeOnboarding();
    useConsentStore.getState().setHasConsented(true);
    router.push('/chat');
  };

  const handleConsentComplete = useCallback((complete: boolean) => {
    setConsentComplete(complete);
  }, []);

  const handleProfileComplete = useCallback((complete: boolean) => {
    setProfileComplete(complete);
    if (complete) {
      handleComplete();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="min-h-screen flex flex-col bg-background" suppressHydrationWarning>
      {/* Header with branding */}
      <header className="border-b bg-card">
        <div className="max-w-3xl mx-auto px-4 py-4 flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center flex-shrink-0">
            <Shield className="w-4 h-4 text-primary-foreground" />
          </div>
          <span className="font-display font-semibold text-lg">Responsible AI</span>
        </div>
      </header>

      {/* Step indicator - breadcrumb style */}
      <nav
        aria-label="Onboarding progress"
        className="border-b bg-card"
      >
        <div className="max-w-3xl mx-auto px-4 py-3 flex items-center gap-2">
          {STEPS.map((step, idx) => {
            const isActive = step.key === currentStep;
            const isPast = STEP_ORDER.indexOf(step.key) < stepIndex;
            return (
              <div key={step.key} className="flex items-center gap-2">
                {idx > 0 && (
                  <span className="text-muted-foreground/40 text-sm" aria-hidden="true">
                    /
                  </span>
                )}
                <span
                  className={cn(
                    'text-sm font-medium transition-colors',
                    isActive && 'text-primary',
                    isPast && 'text-muted-foreground',
                    !isActive && !isPast && 'text-muted-foreground/50'
                  )}
                  aria-current={isActive ? 'step' : undefined}
                >
                  {step.label}
                </span>
              </div>
            );
          })}
        </div>
      </nav>

      {/* Main content area */}
      <main className="flex-1 flex items-start justify-center py-8 px-4">
        <div className="w-full max-w-2xl">
          <AnimatePresence mode="wait" custom={direction}>
            {currentStep === 'welcome' && (
              <motion.div
                key="welcome"
                custom={direction}
                variants={slideVariants}
                initial="enter"
                animate="center"
                exit="exit"
                transition={{ duration: 0.3, ease: 'easeInOut' }}
              >
                <WelcomeContent />
              </motion.div>
            )}
            {currentStep === 'consent' && (
              <motion.div
                key="consent"
                custom={direction}
                variants={slideVariants}
                initial="enter"
                animate="center"
                exit="exit"
                transition={{ duration: 0.3, ease: 'easeInOut' }}
              >
                <ConsentStep onComplete={handleConsentComplete} />
              </motion.div>
            )}
            {currentStep === 'profile' && (
              <motion.div
                key="profile"
                custom={direction}
                variants={slideVariants}
                initial="enter"
                animate="center"
                exit="exit"
                transition={{ duration: 0.3, ease: 'easeInOut' }}
              >
                <ProfileModeSelector onComplete={handleProfileComplete} />
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </main>

      {/* Navigation footer */}
      <footer className="border-t bg-card mt-auto">
        <div className="max-w-3xl mx-auto px-4 py-4 flex items-center justify-between">
          <Button
            variant="ghost"
            onClick={goBack}
            disabled={!canGoBack}
            className="gap-1"
            aria-label="Go back"
          >
            <ChevronLeft className="w-4 h-4" />
            Back
          </Button>

          {currentStep === 'profile' ? null : (
            <Button
              onClick={goNext}
              disabled={!canGoForward()}
              className="gap-1"
              aria-label={
                currentStep === 'welcome'
                  ? 'Continue to privacy settings'
                  : 'Continue to profile'
              }
            >
              Continue
              <ChevronRight className="w-4 h-4" />
            </Button>
          )}
        </div>
      </footer>
    </div>
  );
}

/* ── Welcome step content ─────────────────────────────────────────── */

function WelcomeContent() {
  return (
    <div className="space-y-6">
      <div className="text-center space-y-2">
        <h1 className="font-display text-3xl sm:text-4xl font-semibold tracking-tight text-foreground">
          Welcome to Responsible AI
        </h1>
      </div>

      <div className="space-y-4 text-muted-foreground text-base leading-relaxed max-w-lg mx-auto text-center">
        <p>
          This system connects you with an AI assistant trained on curated,
          reliable sources. It&apos;s designed to provide thoughtful, accurate
          answers to your questions.
        </p>
        <p>
          Before we begin, we&apos;ll ask about your privacy preferences. You&apos;re
          in control of what information is stored.
        </p>
        <p>
          You can update your privacy settings at any time from the Settings
          page.
        </p>
      </div>
    </div>
  );
}
