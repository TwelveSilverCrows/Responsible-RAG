'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import {
  Sparkles,
  User,
  Languages,
  GraduationCap,
  Heart,
  Users,
  Globe,
  Accessibility,
  BookOpen,
  FileText,
  MessageSquare,
  ChevronRight,
} from 'lucide-react';
import {
  Carousel,
  CarouselContent,
  CarouselItem,
  CarouselNext,
  CarouselPrevious,
} from '@/components/ui/carousel';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import type { GenerateProfileResponseDTO, AdaptationFieldDTO } from '@/lib/api';

interface ProfileReviewStepProps {
  result: GenerateProfileResponseDTO;
  onComplete: () => void;
}

/** Maps demographic field keys to icons and colours */
const FIELD_META: Record<
  string,
  { icon: typeof User; color: string; bg: string }
> = {
  sex_at_birth: { icon: Users, color: 'text-violet-500', bg: 'bg-violet-50 dark:bg-violet-950/30' },
  gender: { icon: Heart, color: 'text-pink-500', bg: 'bg-pink-50 dark:bg-pink-950/30' },
  age_group: { icon: User, color: 'text-blue-500', bg: 'bg-blue-50 dark:bg-blue-950/30' },
  primary_language: { icon: Languages, color: 'text-emerald-500', bg: 'bg-emerald-50 dark:bg-emerald-950/30' },
  education_level: { icon: GraduationCap, color: 'text-amber-500', bg: 'bg-amber-50 dark:bg-amber-950/30' },
  citizen_status: { icon: Globe, color: 'text-cyan-500', bg: 'bg-cyan-50 dark:bg-cyan-950/30' },
  indigenous_status: { icon: Users, color: 'text-orange-500', bg: 'bg-orange-50 dark:bg-orange-950/30' },
  disability_status: { icon: Accessibility, color: 'text-indigo-500', bg: 'bg-indigo-50 dark:bg-indigo-950/30' },
};

function AdaptationSlide({ field }: { field: AdaptationFieldDTO }) {
  const meta = FIELD_META[field.field] ?? {
    icon: Sparkles,
    color: 'text-muted-foreground',
    bg: 'bg-muted',
  };
  const Icon = meta.icon;

  return (
    <div className="flex flex-col items-center text-center px-4 py-6">
      <div
        className={cn(
          'w-16 h-16 rounded-2xl flex items-center justify-center mb-4',
          meta.bg
        )}
      >
        <Icon className={cn('w-8 h-8', meta.color)} />
      </div>
      <h3 className="font-semibold text-lg text-foreground mb-1">
        {field.label}
      </h3>
      <p className="text-sm text-muted-foreground max-w-xs leading-relaxed">
        {field.value}
      </p>
      <div className="mt-4">
        {field.evidence_found ? (
          <Badge variant="secondary" className="gap-1 text-xs">
            <BookOpen className="w-3 h-3" />
            Research-backed
          </Badge>
        ) : (
          <Badge variant="outline" className="text-xs text-muted-foreground">
            Standard guidance
          </Badge>
        )}
      </div>
    </div>
  );
}

export function ProfileReviewStep({ result, onComplete }: ProfileReviewStepProps) {
  const [showPrompt, setShowPrompt] = useState(false);

  const hasAdaptations =
    result.adaptation_fields.length > 0;
  const hasSources = result.sources_used.length > 0;

  return (
    <div className="space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center space-y-3"
      >
        <div className="flex justify-center">
          <div className="w-14 h-14 rounded-full bg-primary/10 flex items-center justify-center">
            <Sparkles className="w-7 h-7 text-primary" />
          </div>
        </div>
        <div className="space-y-1">
          <h2 className="font-display text-2xl sm:text-3xl font-semibold tracking-tight text-foreground">
            Your personalisation is ready
          </h2>
          <p className="text-muted-foreground text-sm max-w-md mx-auto">
            We&apos;ve tailored the AI to adapt to your needs using{' '}
            {result.sources_used.length > 0
              ? `${result.sources_used.length} research sources`
              : 'standard best practices'}
            .
          </p>
        </div>
      </motion.div>

      {/* Carousel — personalisation dimensions */}
      {hasAdaptations && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-sm text-foreground flex items-center gap-2">
              <User className="w-4 h-4 text-primary" />
              How we personalise your experience
            </h3>
            <span className="text-xs text-muted-foreground">
              {result.fields_provided} dimension{result.fields_provided !== 1 ? 's' : ''}
            </span>
          </div>

          <Carousel
            opts={{
              align: 'start',
              loop: true,
            }}
            className="w-full max-w-sm mx-auto"
          >
            <CarouselContent>
              {result.adaptation_fields.map((field) => (
                <CarouselItem key={field.field}>
                  <AdaptationSlide field={field} />
                </CarouselItem>
              ))}
            </CarouselContent>
            <CarouselPrevious />
            <CarouselNext />
          </Carousel>
        </motion.div>
      )}

      {/* Sources used */}
      {hasSources && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="space-y-3"
        >
          <h3 className="font-semibold text-sm text-foreground flex items-center gap-2">
            <FileText className="w-4 h-4 text-primary" />
            Sources used to build your profile
          </h3>
          <div className="flex flex-wrap gap-2">
            {result.sources_used.map((title, idx) => (
              <Badge
                key={idx}
                variant="secondary"
                className="text-xs font-normal max-w-full truncate"
              >
                {title}
              </Badge>
            ))}
          </div>
        </motion.div>
      )}

      {/* Generated prompt (collapsible) */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.45 }}
      >
        <button
          onClick={() => setShowPrompt(!showPrompt)}
          className="flex items-center gap-2 text-sm text-primary hover:text-primary/80 font-medium transition-colors"
        >
          <MessageSquare className="w-4 h-4" />
          {showPrompt ? 'Hide' : 'Show'} generated profile prompt
          <ChevronRight
            className={cn(
              'w-4 h-4 transition-transform',
              showPrompt && 'rotate-90'
            )}
          />
        </button>

        {showPrompt && (
          <Card className="mt-3 bg-muted/50">
            <CardContent className="p-4">
              <pre className="text-xs text-muted-foreground whitespace-pre-wrap font-mono leading-relaxed max-h-80 overflow-y-auto">
                {result.prompt}
              </pre>
            </CardContent>
          </Card>
        )}
      </motion.div>

      <Separator />

      {/* Continue button */}
      <div className="text-center">
        <Button
          size="lg"
          onClick={onComplete}
          className="gap-2"
        >
          <MessageSquare className="w-4 h-4" />
          Start chatting
        </Button>
        <p className="text-xs text-muted-foreground mt-3">
          You can review or change your preferences anytime in Settings.
        </p>
      </div>
    </div>
  );
}
