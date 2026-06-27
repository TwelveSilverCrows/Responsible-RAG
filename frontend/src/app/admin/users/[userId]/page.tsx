'use client';

import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  Loader2,
  ArrowLeft,
  Shield,
  ShieldOff,
  Mail,
  Calendar,
  MessageSquare,
  FileText,
  Trash2,
  User as UserIcon,
  Lock,
  Unlock,
  Eye,
  EyeOff,
  CheckCircle2,
  XCircle,
  ChevronRight,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { AdminShell } from '@/components/layout/AdminShell';
import { AdminGuard } from '@/components/AuthGuard';
import { api, type UserAdminDTO, type UserProfileAdminDTO, type UserConsentAdminDTO, type UserActivityDTO, type UserConversationItemDTO } from '@/lib/api';
import { format } from 'date-fns';

type Tab = 'overview' | 'profile' | 'conversations';

export default function UserDetailPage() {
  const { userId } = useParams<{ userId: string }>();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [user, setUser] = useState<UserAdminDTO | null>(null);
  const [profile, setProfile] = useState<UserProfileAdminDTO | null>(null);
  const [consent, setConsent] = useState<UserConsentAdminDTO | null>(null);
  const [activity, setActivity] = useState<UserActivityDTO | null>(null);
  const [conversations, setConversations] = useState<UserConversationItemDTO[]>([]);
  const [convTotal, setConvTotal] = useState(0);
  const [activeTab, setActiveTab] = useState<Tab>('overview');
  const [showRedacted, setShowRedacted] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    if (!userId) return;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const [userData, profileData, consentData, activityData] = await Promise.all([
          api.users.get(userId),
          api.users.getProfile(userId),
          api.users.getConsent(userId),
          api.users.getActivity(userId),
        ]);
        setUser(userData);
        setProfile(profileData);
        setConsent(consentData);
        setActivity(activityData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load user');
      } finally {
        setLoading(false);
      }
    })();
  }, [userId]);

  async function loadConversations(page = 1) {
    if (!userId) return;
    try {
      const data = await api.users.getConversations(userId, page);
      setConversations(data.conversations);
      setConvTotal(data.total);
    } catch {
      // Conversations are only available with consent
      setConversations([]);
      setConvTotal(0);
    }
  }

  useEffect(() => {
    if (activeTab === 'conversations') {
      loadConversations();
    }
  }, [activeTab]);

  async function handleDelete() {
    if (!userId) return;
    setDeleting(true);
    try {
      await api.users.delete(userId);
      navigate('/admin/users');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete user');
      setDeleting(false);
    }
  }

  if (loading) {
    return (
      <AdminGuard>
      <AdminShell>
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
        </div>
      </AdminShell>
      </AdminGuard>
    );
  }

  if (error || !user) {
    return (
      <AdminGuard>
      <AdminShell>
        <div className="text-center py-12">
          <p className="text-destructive mb-2">{error || 'User not found'}</p>
          <Button variant="outline" onClick={() => navigate('/admin/users')}>
            Back to users
          </Button>
        </div>
      </AdminShell>
      </AdminGuard>
    );
  }

  return (
    <AdminGuard>
    <AdminShell>
      <div className="space-y-6">
        {/* Back link */}
        <Button variant="ghost" size="sm" asChild className="-ml-2">
          <Link to="/admin/users">
            <ArrowLeft className="w-4 h-4 mr-1" />
            Back to users
          </Link>
        </Button>

        {/* User header */}
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-full bg-primary/10 flex items-center justify-center">
              <UserIcon className="w-7 h-7 text-primary" />
            </div>
            <div>
              <h1 className="text-2xl font-semibold font-display">{user.name || 'Unnamed User'}</h1>
              <p className="text-sm text-muted-foreground">{user.email}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {user.role === 'admin' ? (
              <Badge variant="default" className="bg-amber-600">
                <Shield className="w-3 h-3 mr-1" />
                Admin
              </Badge>
            ) : (
              <Badge variant="secondary">
                <ShieldOff className="w-3 h-3 mr-1" />
                User
              </Badge>
            )}
            {user.verified ? (
              <Badge variant="outline" className="text-emerald-600 border-emerald-300">
                <CheckCircle2 className="w-3 h-3 mr-1" />
                Verified
              </Badge>
            ) : (
              <Badge variant="outline" className="text-muted-foreground">
                <XCircle className="w-3 h-3 mr-1" />
                Unverified
              </Badge>
            )}
            <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
              <DialogTrigger asChild>
                <Button variant="destructive" size="sm">
                  <Trash2 className="w-4 h-4 mr-1" />
                  Delete
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Delete User</DialogTitle>
                  <DialogDescription>
                    This will permanently delete <strong>{user.name || user.email}</strong> and all
                    associated data — profile, consent, conversations, and messages.
                    This action cannot be undone.
                  </DialogDescription>
                </DialogHeader>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setDeleteDialogOpen(false)}>
                    Cancel
                  </Button>
                  <Button variant="destructive" onClick={handleDelete} disabled={deleting}>
                    {deleting ? (
                      <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Deleting...</>
                    ) : (
                      'Delete User'
                    )}
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 border-b">
          {([
            { key: 'overview', label: 'Overview' },
            { key: 'profile', label: 'Demographic Profile' },
            { key: 'conversations', label: 'Conversations' },
          ] as { key: Tab; label: string }[]).map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.key
                  ? 'border-primary text-primary'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* ── Overview tab ──────────────────────────────────────────────── */}
        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Account info */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Account</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Provider</span>
                  <span className="capitalize">{user.provider}</span>
                </div>
                <Separator />
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Onboarding</span>
                  <span>{user.onboarding_completed ? 'Completed' : 'Not completed'}</span>
                </div>
                <Separator />
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Joined</span>
                  <span>{user.created_at ? format(new Date(user.created_at), 'MMM d, yyyy HH:mm') : '—'}</span>
                </div>
              </CardContent>
            </Card>

            {/* Activity */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Activity</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground flex items-center gap-1.5">
                    <MessageSquare className="w-3.5 h-3.5" /> Conversations
                  </span>
                  <span className="font-medium">{activity?.conversation_count ?? '—'}</span>
                </div>
                <Separator />
                <div className="flex justify-between">
                  <span className="text-muted-foreground flex items-center gap-1.5">
                    <FileText className="w-3.5 h-3.5" /> Messages
                  </span>
                  <span className="font-medium">{activity?.message_count ?? '—'}</span>
                </div>
                <Separator />
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Last conversation</span>
                  <span className="text-xs">
                    {activity?.last_conversation_at
                      ? format(new Date(activity.last_conversation_at), 'MMM d, yyyy HH:mm')
                      : '—'}
                  </span>
                </div>
              </CardContent>
            </Card>

            {/* Consent */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Privacy & Consent</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Profile mode</span>
                  <Badge variant="outline">{consent?.profile_mode || 'general'}</Badge>
                </div>
                <Separator />
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Has consented</span>
                  {consent?.has_consented ? (
                    <Badge variant="outline" className="text-emerald-600 border-emerald-300">
                      <CheckCircle2 className="w-3 h-3 mr-1" /> Yes
                    </Badge>
                  ) : (
                    <Badge variant="outline" className="text-muted-foreground">
                      <XCircle className="w-3 h-3 mr-1" /> No
                    </Badge>
                  )}
                </div>
                <Separator />
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Research data consent</span>
                  {consent?.research_data_consent ? (
                    <Badge variant="outline" className="text-emerald-600 border-emerald-300">
                      <Unlock className="w-3 h-3 mr-1" /> Granted
                    </Badge>
                  ) : (
                    <Badge variant="outline" className="text-muted-foreground">
                      <Lock className="w-3 h-3 mr-1" /> Not granted
                    </Badge>
                  )}
                </div>
                {consent?.consented_at && (
                  <>
                    <Separator />
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Consented at</span>
                      <span className="text-xs">{format(new Date(consent.consented_at), 'MMM d, yyyy HH:mm')}</span>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>

            {/* Data sharing status */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Shared Information</CardTitle>
                <CardDescription>
                  What data the user has agreed to share for research
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                {profile?.redacted ? (
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <EyeOff className="w-4 h-4" />
                    <span>Profile details are not available — the user has not granted research data consent.</span>
                  </div>
                ) : profile?.has_profile ? (
                  <div className="flex items-center gap-2 text-emerald-600">
                    <Eye className="w-4 h-4" />
                    <span>Demographic data is visible (research consent granted).</span>
                  </div>
                ) : (
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <UserIcon className="w-4 h-4" />
                    <span>No demographic profile has been created.</span>
                  </div>
                )}

                {consent?.research_data_consent && (
                  <>
                    <Separator />
                    <div className="flex items-center gap-2 text-emerald-600">
                      <Unlock className="w-4 h-4" />
                      <span>Conversation data available for review.</span>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => { setActiveTab('conversations'); loadConversations(); }}
                    >
                      <MessageSquare className="w-3.5 h-3.5 mr-1.5" />
                      View conversations
                    </Button>
                  </>
                )}
              </CardContent>
            </Card>
          </div>
        )}

        {/* ── Profile tab ────────────────────────────────────────────────── */}
        {activeTab === 'profile' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {profile?.redacted ? (
              <Card className="lg:col-span-2">
                <CardContent className="py-12 text-center text-muted-foreground">
                  <EyeOff className="w-8 h-8 mx-auto mb-3" />
                  <p>This user has not granted research data consent.</p>
                  <p className="text-sm mt-1">Demographic details are private.</p>
                </CardContent>
              </Card>
            ) : profile?.has_profile && profile.data ? (
              <>
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Demographics</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Preferred name</span>
                      <span>{profile.data.preferred_name || '—'}</span>
                    </div>
                    <Separator />
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Age range</span>
                      <span className="capitalize">{profile.data.age_range?.replace(/_/g, ' – ') || '—'}</span>
                    </div>
                    <Separator />
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Gender identity</span>
                      <span>{profile.data.gender_identity?.join(', ') || '—'}</span>
                    </div>
                    <Separator />
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Pronouns</span>
                      <span>{profile.data.pronouns || '—'}</span>
                    </div>
                    <Separator />
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Primary language</span>
                      <span>{profile.data.primary_language || '—'}</span>
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Additional Info</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Education level</span>
                      <span className="capitalize">{profile.data.education_level?.replace(/_/g, ' ') || '—'}</span>
                    </div>
                    <Separator />
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Immigration status</span>
                      <span className="capitalize">{profile.data.immigration_status?.replace(/_/g, ' ') || '—'}</span>
                    </div>
                    <Separator />
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Indigenous identity</span>
                      <span className="capitalize">{profile.data.indigenous_identity?.replace(/_/g, ' ') || '—'}</span>
                    </div>
                    <Separator />
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Disability</span>
                      <span>{profile.data.disability?.join(', ') || '—'}</span>
                    </div>
                    <Separator />
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">AI literacy comfort</span>
                      <span>{profile.data.literacy_comfort_ai != null ? `${profile.data.literacy_comfort_ai}/5` : '—'}</span>
                    </div>
                  </CardContent>
                </Card>
              </>
            ) : (
              <Card className="lg:col-span-2">
                <CardContent className="py-12 text-center text-muted-foreground">
                  <UserIcon className="w-8 h-8 mx-auto mb-3" />
                  <p>This user has not created a demographic profile.</p>
                </CardContent>
              </Card>
            )}
          </div>
        )}

        {/* ── Conversations tab ──────────────────────────────────────────── */}
        {activeTab === 'conversations' && (
          <div>
            {!consent?.research_data_consent ? (
              <Card>
                <CardContent className="py-12 text-center text-muted-foreground">
                  <Lock className="w-8 h-8 mx-auto mb-3" />
                  <p>This user has not granted research data consent.</p>
                  <p className="text-sm mt-1">Conversations are private and cannot be viewed.</p>
                </CardContent>
              </Card>
            ) : conversations.length === 0 ? (
              <Card>
                <CardContent className="py-12 text-center text-muted-foreground">
                  <MessageSquare className="w-8 h-8 mx-auto mb-3" />
                  <p>No conversations found.</p>
                </CardContent>
              </Card>
            ) : (
              <div className="border rounded-lg overflow-hidden">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Title</TableHead>
                      <TableHead>Profile Key</TableHead>
                      <TableHead>Messages</TableHead>
                      <TableHead>Last Updated</TableHead>
                      <TableHead>Created</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {conversations.map((conv) => (
                      <TableRow key={conv.id}>
                        <TableCell className="font-medium">{conv.title}</TableCell>
                        <TableCell>
                          {conv.profile_key ? (
                            <Badge variant="outline">{conv.profile_key}</Badge>
                          ) : (
                            <span className="text-muted-foreground">—</span>
                          )}
                        </TableCell>
                        <TableCell className="text-muted-foreground">{conv.message_count}</TableCell>
                        <TableCell className="text-sm text-muted-foreground whitespace-nowrap">
                          {conv.updated_at ? format(new Date(conv.updated_at), 'MMM d, yyyy HH:mm') : '—'}
                        </TableCell>
                        <TableCell className="text-sm text-muted-foreground whitespace-nowrap">
                          {conv.created_at ? format(new Date(conv.created_at), 'MMM d, yyyy') : '—'}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
            {convTotal > 20 && (
              <p className="text-sm text-muted-foreground mt-2">
                Showing 20 of {convTotal} conversations
              </p>
            )}
          </div>
        )}
      </div>
    </AdminShell>
    </AdminGuard>
  );
}
