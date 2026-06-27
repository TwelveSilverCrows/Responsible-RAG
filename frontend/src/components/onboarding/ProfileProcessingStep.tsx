'use client';

import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Sparkles,
  Brain,
  FileSearch,
  MessageSquare,
  CheckCircle2,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import type { GenerateProfileResponseDTO } from '@/lib/api';

interface ProfileProcessingStepProps {
  onComplete: (result: GenerateProfileResponseDTO) => void;
  userProfile: Record<string, string>;
}

type ProcessingStage = 'preparing' | 'retrieving' | 'generating' | 'done';

const STAGES: { key: ProcessingStage; icon: typeof Sparkles; label: string; description: string }[] = [
  {
    key: 'preparing',
    icon: Brain,
    label: 'Analysing your profile',
    description: 'Understanding your preferences and needs...',
  },
  {
    key: 'retrieving',
    icon: FileSearch,
    label: 'Finding relevant sources',
    description: 'Searching our knowledge base for evidence-based guidance...',
  },
  {
    key: 'generating',
    icon: MessageSquare,
    label: 'Crafting your personalised profile',
    description: 'Building communication rules tailored to you...',
  },
  {
    key: 'done',
    icon: CheckCircle2,
    label: 'Profile ready!',
    description: 'Your personalised experience has been created.',
  },
];

export function ProfileProcessingStep({ onComplete, userProfile }: ProfileProcessingStepProps) {
  const [stage, setStage] = useState<ProcessingStage>('preparing');
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function generate() {
      try {
        // Stage 1: preparing
        setStage('preparing');
        await new Promise((r) => setTimeout(r, 800));

        if (cancelled) return;

        // Stage 2: retrieving
        setStage('retrieving');
        setProgress(25);
        await new Promise((r) => setTimeout(r, 600));

        if (cancelled) return;

        // Stage 3: generating — call the API
        setStage('generating');
        setProgress(50);

        const { api } = await import('@/lib/api');
        const result = await api.profile.generate({
          user_profile: userProfile,
          user_query: 'Generate my personalised communication profile.',
        });

        if (cancelled) return;

        setProgress(90);

        // Brief pause so the user sees "Profile ready!"
        setStage('done');
        setProgress(100);
        await new Promise((r) => setTimeout(r, 1200));

        if (cancelled) return;
        onComplete(result);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to generate profile');
        }
      }
    }

    generate();

    return () => { cancelled = true; };
  }, [onComplete, userProfile]);

  if (error) {
    return (
      <div className="space-y-6 text-center py-12">
        <div className="flex justify-center">
          <div className="w-14 h-14 rounded-full bg-destructive/10 flex items-center justify-center">
            <Sparkles className="w-7 h-7 text-destructive" />
          </div>
        </div>
        <div className="space-y-2">
          <h2 className="font-display text-2xl font-semibold text-foreground">
            Something went wrong
          </h2>
          <p className="text-muted-foreground text-sm max-w-md mx-auto">
            {error}
          </p>
        </div>
        <button
          onClick={() => { setError(null); setStage('preparing'); setProgress(0); }}
          className="text-primary hover:underline text-sm font-medium"
        >
          Try again
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-10 py-8">
      {/* Progress ring */}
      <div className="flex flex-col items-center gap-4">
        <div className="relative w-24 h-24">
          <svg className="w-24 h-24 -rotate-90" viewBox="0 0 100 100">
            <circle
              cx="50" cy="50" r="42"
              fill="none"
              stroke="hsl(var(--muted))"
              strokeWidth="6"
            />
            <motion.circle
              cx="50" cy="50" r="42"
              fill="none"
              stroke="hsl(var(--primary))"
              strokeWidth="6"
              strokeLinecap="round"
              strokeDasharray={264}
              animate={{ strokeDashoffset: 264 - (264 * progress) / 100 }}
              transition={{ duration: 0.5, ease: 'easeInOut' }}
            />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <motion.div
              key={stage}
              initial={{ scale: 0, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0, opacity: 0 }}
              transition={{ duration: 0.3 }}
            >
              {stage === 'done' ? (
                <CheckCircle2 className="w-8 h-8 text-primary" />
              ) : (
                <Brain className="w-8 h-8 text-primary animate-pulse" />
              )}
            </motion.div>
          </div>
        </div>
      </div>

      {/* Stage label */}
      <div className="text-center space-y-2">
        <AnimatePresence mode="wait">
          <motion.div
            key={stage}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.3 }}
          >
            <h2 className="font-display text-2xl font-semibold text-foreground">
              {STAGES.find((s) => s.key === stage)?.label}
            </h2>
            <p className="text-muted-foreground text-sm mt-2">
              {STAGES.find((s) => s.key === stage)?.description}
            </p>
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Stage timeline */}
      <div className="max-w-sm mx-auto space-y-3">
        {STAGES.filter((s) => s.key !== 'done').map((s) => {
          const stageOrder = ['preparing', 'retrieving', 'generating'];
          const currentIdx = stageOrder.indexOf(stage);
          const stageIdx = stageOrder.indexOf(s.key);
          const isActive = s.key === stage;
          const isPast = stageIdx < currentIdx;

          return (
            <div
              key={s.key}
              className={cn(
                'flex items-center gap-3 text-sm transition-all duration-300',
                isPast && 'text-muted-foreground/60',
                isActive && 'text-foreground font-medium',
                !isPast && !isActive && 'text-muted-foreground/40'
              )}
            >
              <div
                className={cn(
                  'w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 transition-colors',
                  isPast && 'bg-primary/20 text-primary',
                  isActive && 'bg-primary text-primary-foreground',
                  !isPast && !isActive && 'bg-muted text-muted-foreground/40'
                )}
              >
                {isPast ? (
                  <CheckCircle2 className="w-3.5 h-3.5" />
                ) : (
                  <div className={cn('w-2 h-2 rounded-full bg-current')} />
                )}
              </div>
              <span>{s.label}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
