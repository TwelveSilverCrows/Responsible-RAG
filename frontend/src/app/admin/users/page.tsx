'use client';

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Loader2,
  Search,
  Trash2,
  Shield,
  ShieldOff,
  Mail,
  Calendar,
  MessageSquare,
  FileText,
  ChevronRight,
  UserCheck,
  UserX,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
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
import { api, type UserAdminDTO, type UserStatsDTO } from '@/lib/api';
import { format } from 'date-fns';

export default function AdminUsersPage() {
  const [users, setUsers] = useState<UserAdminDTO[]>([]);
  const [stats, setStats] = useState<UserStatsDTO | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);

  async function loadUsers() {
    setError(null);
    try {
      const [usersData, statsData] = await Promise.all([
        api.users.list(search || undefined),
        api.users.stats(),
      ]);
      setUsers(usersData);
      setStats(statsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load users');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadUsers();
  }, []);

  // Debounced search
  useEffect(() => {
    if (!loading) {
      const timer = setTimeout(() => loadUsers(), 400);
      return () => clearTimeout(timer);
    }
  }, [search]);

  async function handleDelete() {
    if (!deleteId) return;
    setDeleting(true);
    try {
      await api.users.delete(deleteId);
      setUsers((prev) => prev.filter((u) => u.id !== deleteId));
      setDeleteId(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete user');
    } finally {
      setDeleting(false);
    }
  }

  return (
    <AdminGuard>
    <AdminShell>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-semibold font-display">Users</h1>
            <p className="text-sm text-muted-foreground mt-1">
              Manage registered users, view profiles, and monitor activity
            </p>
          </div>
        </div>

        {/* Error state */}
        {error && (
          <div className="text-center py-4">
            <p className="text-sm text-destructive mb-2">{error}</p>
            <Button variant="outline" size="sm" onClick={loadUsers}>
              Retry
            </Button>
          </div>
        )}

        {/* Stat cards */}
        {stats && (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
            <Card>
              <CardHeader className="pb-1.5">
                <CardDescription className="text-xs flex items-center gap-1.5">
                  <UserCheck className="w-3.5 h-3.5" />
                  Total Users
                </CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold">{stats.total_users}</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-1.5">
                <CardDescription className="text-xs flex items-center gap-1.5">
                  <Shield className="w-3.5 h-3.5" />
                  Admins
                </CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold">{stats.admin_users}</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-1.5">
                <CardDescription className="text-xs flex items-center gap-1.5">
                  <FileText className="w-3.5 h-3.5" />
                  With Profiles
                </CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold">{stats.users_with_profiles}</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-1.5">
                <CardDescription className="text-xs flex items-center gap-1.5">
                  <MessageSquare className="w-3.5 h-3.5" />
                  Conversations
                </CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold">{stats.total_conversations}</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-1.5">
                <CardDescription className="text-xs flex items-center gap-1.5">
                  <Search className="w-3.5 h-3.5" />
                  Research Consent
                </CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold">{stats.research_data_consent}</p>
                <p className="text-xs text-muted-foreground">of {stats.consent_granted} consented</p>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Search */}
        <div className="relative max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Search by name or email..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>

        {/* Loading */}
        {loading && (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
          </div>
        )}

        {/* Users table */}
        {!loading && !error && (
          <div className="border rounded-lg overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>Verified</TableHead>
                  <TableHead>Profile</TableHead>
                  <TableHead>Consent</TableHead>
                  <TableHead>Conversations</TableHead>
                  <TableHead>Joined</TableHead>
                  <TableHead className="w-12"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {users.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={9} className="text-center text-muted-foreground py-8">
                      {search ? 'No users match your search' : 'No users registered yet'}
                    </TableCell>
                  </TableRow>
                )}
                {users.map((user) => (
                  <TableRow key={user.id}>
                    <TableCell>
                      <Link
                        to={`/admin/users/${user.id}`}
                        className="font-medium hover:text-primary transition-colors flex items-center gap-1.5"
                      >
                        {user.name || '—'}
                        <ChevronRight className="w-3.5 h-3.5 text-muted-foreground" />
                      </Link>
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      <span className="flex items-center gap-1.5">
                        <Mail className="w-3.5 h-3.5" />
                        {user.email}
                      </span>
                    </TableCell>
                    <TableCell>
                      {user.role === 'admin' ? (
                        <Badge variant="default" className="bg-amber-600 hover:bg-amber-700">
                          <Shield className="w-3 h-3 mr-1" />
                          Admin
                        </Badge>
                      ) : (
                        <Badge variant="secondary">
                          <ShieldOff className="w-3 h-3 mr-1" />
                          User
                        </Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      {user.verified ? (
                        <Badge variant="outline" className="text-emerald-600 border-emerald-300">
                          Verified
                        </Badge>
                      ) : (
                        <Badge variant="outline" className="text-muted-foreground">
                          Unverified
                        </Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      {user.has_profile ? (
                        <Badge variant="outline" className={user.profile_mode === 'full' ? 'text-blue-600 border-blue-300' : ''}>
                          {user.profile_mode}
                        </Badge>
                      ) : (
                        <span className="text-muted-foreground text-sm">—</span>
                      )}
                    </TableCell>
                    <TableCell>
                      {user.research_data_consent ? (
                        <Badge variant="outline" className="text-emerald-600 border-emerald-300">
                          Shared
                        </Badge>
                      ) : user.has_consent ? (
                        <Badge variant="outline" className="text-muted-foreground">
                          No share
                        </Badge>
                      ) : (
                        <span className="text-muted-foreground text-sm">—</span>
                      )}
                    </TableCell>
                    <TableCell className="text-muted-foreground text-sm">
                      {user.conversation_count}
                    </TableCell>
                    <TableCell className="text-muted-foreground text-sm whitespace-nowrap">
                      <span className="flex items-center gap-1.5">
                        <Calendar className="w-3.5 h-3.5" />
                        {user.created_at ? format(new Date(user.created_at), 'MMM d, yyyy') : '—'}
                      </span>
                    </TableCell>
                    <TableCell>
                      <Dialog>
                        <DialogTrigger asChild>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="text-muted-foreground hover:text-destructive"
                            onClick={() => setDeleteId(user.id)}
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </DialogTrigger>
                        <DialogContent>
                          <DialogHeader>
                            <DialogTitle>Delete User</DialogTitle>
                            <DialogDescription>
                              This will permanently delete <strong>{user.name || user.email}</strong> and all
                              associated data — profile, consent preferences, conversations, and messages.
                              This action cannot be undone.
                            </DialogDescription>
                          </DialogHeader>
                          <DialogFooter>
                            <Button variant="outline" onClick={() => setDeleteId(null)}>
                              Cancel
                            </Button>
                            <Button
                              variant="destructive"
                              onClick={handleDelete}
                              disabled={deleting}
                            >
                              {deleting ? (
                                <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Deleting...</>
                              ) : (
                                'Delete User'
                              )}
                            </Button>
                          </DialogFooter>
                        </DialogContent>
                      </Dialog>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </div>
    </AdminShell>
    </AdminGuard>
  );
}
