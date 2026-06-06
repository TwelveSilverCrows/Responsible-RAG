'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageCircle, Heart, CheckCircle2 } from 'lucide-react';
import { AppShell } from '@/components/layout/AppShell';
import { AuthGuard } from '@/components/AuthGuard';
import { ClarityFeedbackForm } from '@/components/feedback/ClarityFeedbackForm';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';

export default function FeedbackPage() {
  const [showForm, setShowForm] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  return (
    <AuthGuard>
      <AppShell>
        <div className="max-w-2xl mx-auto px-4 py-8 sm:py-12">
          <div className="space-y-8">
            {/* Page header */}
            <div>
              <h1 className="font-display text-2xl font-semibold text-foreground">
                Feedback
              </h1>
              <p className="text-muted-foreground text-sm mt-1">
                Help us improve this tool. Your feedback is anonymous and voluntary.
              </p>
            </div>

            {submitted ? (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.3 }}
              >
                <Card className="border-primary/20">
                  <CardContent className="py-12 flex flex-col items-center gap-4 text-center">
                    <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center">
                      <CheckCircle2 className="w-8 h-8 text-primary" />
                    </div>
                    <div className="space-y-1.5">
                      <h2 className="font-display text-xl font-semibold">Thank you!</h2>
                      <p className="text-sm text-muted-foreground max-w-sm">
                        Your feedback has been recorded. It helps us make this tool better
                        for everyone, especially communities that are often underserved by
                        technology.
                      </p>
                    </div>
                    <Button
                      variant="outline"
                      onClick={() => {
                        setSubmitted(false);
                        setShowForm(false);
                      }}
                    >
                      Submit more feedback
                    </Button>
                  </CardContent>
                </Card>
              </motion.div>
            ) : showForm ? (
              <AnimatePresence>
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.3 }}
                >
                  <ClarityFeedbackForm
                    onSubmit={() => setSubmitted(true)}
                    onDismiss={() => setShowForm(false)}
                  />
                </motion.div>
              </AnimatePresence>
            ) : (
              <div className="space-y-6">
                {/* General feedback card */}
                <Card>
                  <CardHeader>
                    <div className="flex items-start gap-3">
                      <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                        <MessageCircle className="w-5 h-5 text-primary" />
                      </div>
                      <div>
                        <CardTitle className="text-base font-display">
                          Share your experience
                        </CardTitle>
                        <CardDescription className="mt-1">
                          Tell us how the AI responses have been working for you. Was the
                          language clear? Did the response address your concern? Your
                          answers help us improve for everyone.
                        </CardDescription>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <Button onClick={() => setShowForm(true)} className="gap-2">
                      <MessageCircle className="w-4 h-4" />
                      Start feedback form
                    </Button>
                  </CardContent>
                </Card>

                <Separator />

                {/* Why feedback matters */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base font-display">
                      Why does feedback matter?
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3 text-sm text-muted-foreground">
                    <p>
                      This system is designed to serve diverse communities, including
                      people who are often underserved by technology. Your feedback helps
                      us understand whether the AI is communicating clearly and
                      respectfully for people of different backgrounds, abilities, and
                      comfort levels with technology.
                    </p>
                    <p>
                      Even brief feedback — a thumbs up or down, or a short comment —
                      makes a real difference. All feedback is anonymized and never linked
                      to your identity unless you choose to share it.
                    </p>
                    <div className="flex items-center gap-2 pt-2">
                      <Heart className="w-4 h-4 text-rose-500 flex-shrink-0" />
                      <span className="text-xs font-medium text-foreground">
                        Every voice matters in building responsible AI.
                      </span>
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}
          </div>
        </div>
      </AppShell>
    </AuthGuard>
  );
}
