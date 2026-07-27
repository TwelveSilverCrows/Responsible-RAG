'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ThumbsUp, ThumbsDown, X, Heart, Clock } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { cn } from '@/lib/utils';

interface ClarityFeedbackFormProps {
  conversationId?: string;
  onDismiss?: () => void;
  onSubmit?: (feedback: ClarityFeedbackData) => void;
}

interface ClarityFeedbackData {
  thumbDirection: 'up' | 'down' | null;
  clarityRating: number | null;
  languageAppropriate: 'yes' | 'somewhat' | 'no' | null;
  unclearText: string;
  feelingRating: number | null;
}

const CLARITY_LABELS: Record<number, string> = {
  1: 'Not at all clear',
  2: 'Slightly clear',
  3: 'Moderately clear',
  4: 'Very clear',
  5: 'Completely clear',
};

const FEELING_EMOJIS = [
  { value: 1, emoji: '😕', label: 'Confused' },
  { value: 2, emoji: '😐', label: 'Neutral' },
  { value: 3, emoji: '🙂', label: 'Pleased' },
  { value: 4, emoji: '😊', label: 'Very satisfied' },
];

export function ClarityFeedbackForm({
  conversationId,
  onDismiss,
  onSubmit,
}: ClarityFeedbackFormProps) {
  const [thumbDirection, setThumbDirection] = useState<'up' | 'down' | null>(
    null
  );
  const [clarityRating, setClarityRating] = useState<number | null>(null);
  const [languageAppropriate, setLanguageAppropriate] = useState<
    'yes' | 'somewhat' | 'no' | null
  >(null);
  const [unclearText, setUnclearText] = useState('');
  const [feelingRating, setFeelingRating] = useState<number | null>(null);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [isDismissed, setIsDismissed] = useState(false);

  const handleDismiss = () => {
    setIsDismissed(true);
    onDismiss?.();
  };

  const handleSubmit = () => {
    const feedback: ClarityFeedbackData = {
      thumbDirection,
      clarityRating,
      languageAppropriate,
      unclearText: unclearText.trim() || '',
      feelingRating,
    };

    console.log('Clarity feedback submitted:', {
      conversationId,
      ...feedback,
    });

    onSubmit?.(feedback);
    setIsSubmitted(true);
  };

  if (isDismissed) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -10 }}
        transition={{ duration: 0.3 }}
      >
        <Card className="border-muted-foreground/15 bg-card">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CardTitle className="text-base font-display">
                  Help us improve
                </CardTitle>
              </div>
              <button
                type="button"
                onClick={handleDismiss}
                className="text-muted-foreground hover:text-foreground transition-colors p-0.5"
                aria-label="Dismiss feedback form"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <p className="text-xs text-muted-foreground flex items-center gap-1.5">
              <Clock className="w-3 h-3" />
              These questions are optional and take about 30 seconds. No
              identifying information is collected.
            </p>
          </CardHeader>

          <CardContent>
            {isSubmitted ? (
              /* ── Thank you state ── */
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="flex flex-col items-center gap-2 py-4 text-center"
              >
                <Heart className="w-8 h-8 text-primary" />
                <p className="text-sm font-medium text-foreground">
                  Thank you for your feedback
                </p>
                <p className="text-xs text-muted-foreground">
                  Your input helps us make this tool better for everyone.
                </p>
              </motion.div>
            ) : (
              /* ── Feedback form ── */
              <div className="space-y-6">
                {/* Thumbs up / down */}
                <div className="space-y-2">
                  <Label className="text-sm">Overall impression</Label>
                  <div className="flex items-center gap-2">
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      className={cn(
                        'gap-1.5',
                        thumbDirection === 'up' &&
                          'bg-primary/10 border-primary/30 text-primary hover:bg-primary/20'
                      )}
                      onClick={() => setThumbDirection('up')}
                      aria-label="Positive response"
                    >
                      <ThumbsUp
                        className={cn(
                          'w-4 h-4',
                          thumbDirection === 'up' && 'fill-primary'
                        )}
                      />
                      Helpful
                    </Button>
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      className={cn(
                        'gap-1.5',
                        thumbDirection === 'down' &&
                          'bg-destructive/10 border-destructive/30 text-destructive hover:bg-destructive/20'
                      )}
                      onClick={() => setThumbDirection('down')}
                      aria-label="Negative response"
                    >
                      <ThumbsDown
                        className={cn(
                          'w-4 h-4',
                          thumbDirection === 'down' && 'fill-destructive'
                        )}
                      />
                      Not helpful
                    </Button>
                  </div>
                </div>

                <Separator />

                {/* Clarity rating */}
                <div className="space-y-3">
                  <Label className="text-sm">
                    Did the response clearly address your concern?
                  </Label>
                  <RadioGroup
                    value={clarityRating?.toString() ?? ''}
                    onValueChange={(val) => setClarityRating(Number(val))}
                    className="space-y-1.5"
                  >
                    {([1, 2, 3, 4, 5] as const).map((num) => (
                      <div key={num} className="flex items-center gap-2.5">
                        <RadioGroupItem
                          value={num.toString()}
                          id={`clarity-${num}`}
                        />
                        <Label
                          htmlFor={`clarity-${num}`}
                          className="text-sm font-normal cursor-pointer flex items-center gap-2"
                        >
                          <span className="w-4 text-center font-medium text-muted-foreground">
                            {num}
                          </span>
                          <span className="text-muted-foreground">
                            {CLARITY_LABELS[num]}
                          </span>
                        </Label>
                      </div>
                    ))}
                  </RadioGroup>
                </div>

                <Separator />

                {/* Language appropriateness */}
                <div className="space-y-3">
                  <Label className="text-sm">
                    Did the language feel appropriate for you?
                  </Label>
                  <RadioGroup
                    value={languageAppropriate ?? ''}
                    onValueChange={(val) =>
                      setLanguageAppropriate(
                        val as 'yes' | 'somewhat' | 'no'
                      )
                    }
                    className="space-y-1.5"
                  >
                    {[
                      { value: 'yes', label: 'Yes, it was clear and natural' },
                      {
                        value: 'somewhat',
                        label: 'Somewhat — it was okay but could be better',
                      },
                      { value: 'no', label: 'No, it felt off or confusing' },
                    ].map((opt) => (
                      <div key={opt.value} className="flex items-center gap-2.5">
                        <RadioGroupItem
                          value={opt.value}
                          id={`lang-${opt.value}`}
                        />
                        <Label
                          htmlFor={`lang-${opt.value}`}
                          className="text-sm font-normal cursor-pointer"
                        >
                          {opt.label}
                        </Label>
                      </div>
                    ))}
                  </RadioGroup>
                </div>

                <Separator />

                {/* Unclear or confusing */}
                <div className="space-y-2">
                  <Label className="text-sm" htmlFor="unclear-text">
                    Was anything unclear or confusing?{' '}
                    <span className="text-muted-foreground font-normal">
                      (optional)
                    </span>
                  </Label>
                  <Textarea
                    id="unclear-text"
                    value={unclearText}
                    onChange={(e) => setUnclearText(e.target.value)}
                    placeholder="Tell us what could be clearer..."
                    className="text-sm min-h-[60px] resize-none"
                    rows={2}
                  />
                </div>

                <Separator />

                {/* Feeling emoji scale */}
                <div className="space-y-3">
                  <Label className="text-sm">
                    How did you feel during this conversation?{' '}
                    <span className="text-muted-foreground font-normal">
                      (optional)
                    </span>
                  </Label>
                  <div className="flex items-center gap-3">
                    {FEELING_EMOJIS.map((item) => (
                      <button
                        key={item.value}
                        type="button"
                        onClick={() => setFeelingRating(item.value)}
                        className={cn(
                          'flex flex-col items-center gap-1 p-2 rounded-lg transition-all',
                          feelingRating === item.value
                            ? 'bg-primary/10 ring-2 ring-primary/30'
                            : 'hover:bg-muted/50'
                        )}
                        aria-label={item.label}
                        aria-pressed={feelingRating === item.value}
                      >
                        <span className="text-2xl leading-none">
                          {item.emoji}
                        </span>
                        <span className="text-[10px] text-muted-foreground">
                          {item.label}
                        </span>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Submit */}
                <div className="flex justify-end pt-1">
                  <Button
                    type="button"
                    size="sm"
                    onClick={handleSubmit}
                    className="gap-1.5"
                  >
                    Submit feedback
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>
    </AnimatePresence>
  );
}
