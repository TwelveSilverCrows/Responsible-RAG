'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ThumbsUp, ThumbsDown, X, Heart } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent } from '@/components/ui/card';
import { cn } from '@/lib/utils';

interface PostChatFeedbackProps {
  conversationId?: string;
  onDismiss?: () => void;
}

type FeedbackState = 'idle' | 'selected' | 'submitted';

export function PostChatFeedback({
  conversationId,
  onDismiss,
}: PostChatFeedbackProps) {
  const [feedbackState, setFeedbackState] = useState<FeedbackState>('idle');
  const [thumbSelection, setThumbSelection] = useState<
    'up' | 'down' | null
  >(null);
  const [comment, setComment] = useState('');
  const [isDismissed, setIsDismissed] = useState(false);

  const handleThumbClick = (direction: 'up' | 'down') => {
    setThumbSelection(direction);
    setFeedbackState('selected');
  };

  const handleSubmit = () => {
    // In a real app, this would send feedback to the backend
    console.log('Feedback submitted:', {
      conversationId,
      thumb: thumbSelection,
      comment: comment.trim() || undefined,
    });
    setFeedbackState('submitted');
  };

  const handleDismiss = () => {
    setIsDismissed(true);
    onDismiss?.();
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
        <Card className="border-dashed border-muted-foreground/20 bg-muted/30">
          <CardContent className="p-4">
            {feedbackState === 'submitted' ? (
              /* ── Thank you state ── */
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="flex items-center gap-2 text-sm text-muted-foreground"
              >
                <Heart className="w-4 h-4 text-primary" />
                <span>Thank you for your feedback. It helps us improve.</span>
              </motion.div>
            ) : (
              /* ── Feedback form ── */
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <p className="text-sm text-muted-foreground">
                    Was this response helpful?
                  </p>
                  <button
                    type="button"
                    onClick={handleDismiss}
                    className="text-muted-foreground hover:text-foreground transition-colors p-0.5"
                    aria-label="Dismiss feedback"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>

                <div className="flex items-center gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    className={cn(
                      'gap-1.5',
                      thumbSelection === 'up' &&
                        'bg-primary/10 border-primary/30 text-primary hover:bg-primary/20'
                    )}
                    onClick={() => handleThumbClick('up')}
                    aria-label="Thumbs up"
                  >
                    <ThumbsUp
                      className={cn(
                        'w-4 h-4',
                        thumbSelection === 'up' && 'fill-primary'
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
                      thumbSelection === 'down' &&
                        'bg-destructive/10 border-destructive/30 text-destructive hover:bg-destructive/20'
                    )}
                    onClick={() => handleThumbClick('down')}
                    aria-label="Thumbs down"
                  >
                    <ThumbsDown
                      className={cn(
                        'w-4 h-4',
                        thumbSelection === 'down' && 'fill-destructive'
                      )}
                    />
                    Not helpful
                  </Button>
                </div>

                {thumbSelection && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    transition={{ duration: 0.2 }}
                    className="space-y-2"
                  >
                    <Textarea
                      value={comment}
                      onChange={(e) => setComment(e.target.value)}
                      placeholder="Tell us more... (optional)"
                      className="text-sm min-h-[60px] resize-none"
                      rows={2}
                    />
                    <div className="flex justify-end">
                      <Button
                        type="button"
                        size="sm"
                        onClick={handleSubmit}
                        className="gap-1"
                      >
                        Submit
                      </Button>
                    </div>
                  </motion.div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>
    </AnimatePresence>
  );
}
