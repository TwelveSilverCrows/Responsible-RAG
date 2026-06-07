'use client';

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  UserCheck,
  Lock,
  ArrowRightLeft,
  FileText,
  Trash2,
  MessageSquare,
  AlertTriangle,
  Eye,
} from 'lucide-react';
import { motion } from 'framer-motion';
import { format } from 'date-fns';
import { AppShell } from '@/components/layout/AppShell';
import { AuthGuard } from '@/components/AuthGuard';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { Separator } from '@/components/ui/separator';
import { Badge } from '@/components/ui/badge';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { useConsentStore } from '@/stores/consentStore';
import { useProfileStore } from '@/stores/profileStore';
import { useChatStore } from '@/stores/chatStore';
import { getModeSwitchConfirmation } from '@/lib/utils/privacyHelpers';
import { formatProfileForDisplay } from '@/lib/utils/privacyHelpers';
import { cn } from '@/lib/utils';

export default function SettingsPage() {
  const navigate = useNavigate();
  const consentStore = useConsentStore();
  const profileStore = useProfileStore();
  const chatStore = useChatStore();

  const [showModeDialog, setShowModeDialog] = useState(false);
  const [showViewDataDialog, setShowViewDataDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [deleteConfirmation, setDeleteConfirmation] = useState('');
  const [deletingConvoId, setDeletingConvoId] = useState<string | null>(null);

  const currentMode = consentStore.profileMode ?? 'general';
  const isFull = currentMode === 'full';
  const targetMode = isFull ? 'general' : 'full';
  const confirmation = getModeSwitchConfirmation(currentMode, targetMode);

  const handleModeSwitch = () => {
    if (targetMode === 'general') {
      profileStore.setProfile(null);
      consentStore.setProfileMode('general');
    } else {
      consentStore.setProfileMode('full');
      // Redirect to onboarding profile form
      setShowModeDialog(false);
      navigate('/onboarding/profile');
      return;
    }
    setShowModeDialog(false);
  };

  const handleDeleteAllData = () => {
    if (deleteConfirmation !== 'DELETE') return;
    profileStore.reset();
    consentStore.reset();
    setDeleteConfirmation('');
    setShowDeleteDialog(false);
  };

  const handleDeleteConversation = (id: string) => {
    chatStore.removeConversation(id);
    setDeletingConvoId(null);
  };

  const profileJson =
    profileStore.profile
      ? formatProfileForDisplay(profileStore.profile as unknown as Record<string, unknown>)
      : 'No profile data stored.';

  return (
    <AuthGuard>
    <AppShell>
      <div className="max-w-2xl mx-auto px-4 py-8 sm:py-12">
        <div className="space-y-8">
          {/* Page header */}
          <div>
            <h1 className="font-display text-2xl font-semibold text-foreground">
              Privacy Settings
            </h1>
            <p className="text-muted-foreground text-sm mt-1">
              Manage how your data is used and stored.
            </p>
          </div>

          {/* ── My Privacy Mode ────────────────────────── */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base font-display">
                My Privacy Mode
              </CardTitle>
              <CardDescription className="text-sm">
                Control how much personal information the system uses to tailor
                your experience.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-3 p-3 rounded-lg bg-muted/50">
                <div
                  className={cn(
                    'w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0',
                    isFull ? 'bg-primary/10' : 'bg-muted'
                  )}
                >
                  {isFull ? (
                    <UserCheck className="w-5 h-5 text-primary" />
                  ) : (
                    <Lock className="w-5 h-5 text-muted-foreground" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium">
                    {isFull ? 'Full Profile Mode' : 'General Mode'}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {isFull
                      ? 'Your profile is used to personalize AI responses to your accessibility needs, language preferences, and communication style.'
                      : 'No personal information is stored about you. The AI will provide general responses without adaptation.'}
                  </p>
                </div>
              </div>

              <Button
                variant="outline"
                className="w-full gap-2"
                onClick={() => setShowModeDialog(true)}
              >
                <ArrowRightLeft className="w-4 h-4" />
                Switch to {isFull ? 'General' : 'Full Profile'} Mode
              </Button>
            </CardContent>
          </Card>

          {/* ── Data Consent ───────────────────────────── */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base font-display">
                Data Consent
              </CardTitle>
              <CardDescription className="text-sm">
                Manage how your data contributes to improving the system.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-start justify-between gap-4">
                <div className="space-y-1.5 flex-1">
                  <Label
                    htmlFor="settings-research-consent"
                    className="text-sm font-medium cursor-pointer"
                  >
                    Research data sharing
                  </Label>
                  <p className="text-xs text-muted-foreground leading-relaxed">
                    If enabled, anonymized snippets from your conversations may
                    be used by researchers to study how AI systems can better
                    serve diverse communities. Your identity is never revealed,
                    and you can opt out at any time.
                  </p>
                </div>
                <Switch
                  id="settings-research-consent"
                  checked={consentStore.researchDataConsent}
                  onCheckedChange={consentStore.setResearchDataConsent}
                />
              </div>
            </CardContent>
          </Card>

          {/* ── My Data ────────────────────────────────── */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base font-display">My Data</CardTitle>
              <CardDescription className="text-sm">
                See what we have stored, or delete it all.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <Button
                variant="outline"
                className="w-full gap-2 justify-start"
                onClick={() => setShowViewDataDialog(true)}
              >
                <Eye className="w-4 h-4" />
                View what we have stored about you
              </Button>

              <Button
                variant="outline"
                className="w-full gap-2 justify-start text-destructive hover:text-destructive border-destructive/30 hover:border-destructive/50 hover:bg-destructive/5"
                onClick={() => setShowDeleteDialog(true)}
              >
                <Trash2 className="w-4 h-4" />
                Delete all my data
              </Button>
            </CardContent>
          </Card>

          {/* ── Communications History ─────────────────── */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base font-display">
                Communications History
              </CardTitle>
              <CardDescription className="text-sm">
                {consentStore.researchDataConsent
                  ? 'Your past conversations are listed below. You can delete individual conversations.'
                  : 'No conversation data is stored for your account.'}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {consentStore.researchDataConsent ? (
                chatStore.conversations.length > 0 ? (
                  <div className="space-y-2 max-h-96 overflow-y-auto">
                    {chatStore.conversations.map((convo) => (
                      <div
                        key={convo.id}
                        className="flex items-center justify-between gap-3 p-3 rounded-lg border bg-card"
                      >
                        <div className="min-w-0 flex-1">
                          <p className="text-sm font-medium truncate">
                            {convo.title}
                          </p>
                          <div className="flex items-center gap-2 mt-0.5">
                            <p className="text-xs text-muted-foreground">
                              {format(
                                new Date(convo.createdAt),
                                'MMM d, yyyy'
                              )}
                            </p>
                            <span className="text-xs text-muted-foreground">
                              ·
                            </span>
                            <p className="text-xs text-muted-foreground">
                              {convo.messageCount} message
                              {convo.messageCount !== 1 ? 's' : ''}
                            </p>
                          </div>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-muted-foreground hover:text-destructive flex-shrink-0"
                          onClick={() => setDeletingConvoId(convo.id)}
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-6">
                    <MessageSquare className="w-8 h-8 text-muted-foreground mx-auto mb-2" />
                    <p className="text-sm text-muted-foreground">
                      No conversations yet.
                    </p>
                  </div>
                )
              ) : (
                <div className="text-center py-6">
                  <Lock className="w-8 h-8 text-muted-foreground mx-auto mb-2" />
                  <p className="text-sm text-muted-foreground">
                    No conversation data is stored for your account.
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Enable research data sharing above to manage conversation
                    history.
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* ── Mode Switch Confirmation Dialog ───────────── */}
      <AlertDialog
        open={showModeDialog}
        onOpenChange={(open) => {
          if (!open) return; // intentional friction
          setShowModeDialog(true);
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{confirmation.title}</AlertDialogTitle>
            <AlertDialogDescription>
              {confirmation.description}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel
              onClick={() => setShowModeDialog(false)}
              className="cursor-pointer"
            >
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={handleModeSwitch}
              className={cn(
                confirmation.isDestructive &&
                  'bg-destructive text-destructive-foreground hover:bg-destructive/90'
              )}
            >
              {confirmation.isDestructive
                ? 'Yes, switch to General'
                : 'Yes, switch to Full Profile'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* ── View My Data Dialog ───────────────────────── */}
      <Dialog open={showViewDataDialog} onOpenChange={setShowViewDataDialog}>
        <DialogContent className="sm:max-w-lg max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Your Stored Data</DialogTitle>
            <DialogDescription>
              This is all the information we have stored about you, excluding
              internal identifiers.
            </DialogDescription>
          </DialogHeader>
          <pre className="text-xs bg-muted/50 rounded-md p-4 overflow-x-auto whitespace-pre-wrap break-words font-mono leading-relaxed">
            {profileJson}
          </pre>
        </DialogContent>
      </Dialog>

      {/* ── Delete All Data Dialog ────────────────────── */}
      <AlertDialog
        open={showDeleteDialog}
        onOpenChange={(open) => {
          if (!open) {
            setDeleteConfirmation('');
          }
          setShowDeleteDialog(open);
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-destructive" />
              Delete all your data?
            </AlertDialogTitle>
            <AlertDialogDescription asChild>
              <div className="space-y-3">
                <p>
                  This will permanently delete your profile, consent preferences,
                  and all stored data. This action cannot be undone.
                </p>
                <div className="bg-destructive/5 border border-destructive/20 rounded-md p-3">
                  <p className="text-xs text-destructive font-medium">
                    Please note: Deletion is processed with a 48-hour delay.
                    During this period, you can contact support to cancel the
                    request.
                  </p>
                </div>
                <div className="space-y-2">
                  <Label
                    htmlFor="delete-confirm"
                    className="text-sm font-medium"
                  >
                    Type <strong>DELETE</strong> to confirm
                  </Label>
                  <Input
                    id="delete-confirm"
                    value={deleteConfirmation}
                    onChange={(e) => setDeleteConfirmation(e.target.value)}
                    placeholder="Type DELETE here"
                    className="font-mono"
                  />
                </div>
              </div>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel
              onClick={() => {
                setDeleteConfirmation('');
                setShowDeleteDialog(false);
              }}
              className="cursor-pointer"
            >
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteAllData}
              disabled={deleteConfirmation !== 'DELETE'}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Delete all data
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* ── Delete Conversation Confirmation ──────────── */}
      <AlertDialog
        open={!!deletingConvoId}
        onOpenChange={(open) => {
          if (!open) setDeletingConvoId(null);
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete this conversation?</AlertDialogTitle>
            <AlertDialogDescription>
              This conversation and all its messages will be permanently deleted.
              This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="cursor-pointer">
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                if (deletingConvoId) {
                  handleDeleteConversation(deletingConvoId);
                }
              }}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </AppShell>
    </AuthGuard>
  );
}
