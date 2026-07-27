'use client';

import { useState, useEffect } from 'react';
import {
  ShieldAlert,
  AlertTriangle,
  Info,
  CheckCircle2,
  Clock,
  RefreshCw,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { AdminShell } from '@/components/layout/AdminShell';
import { AdminGuard } from '@/components/AuthGuard';
import { api, type AdminAlertDTO } from '@/lib/api';
import { format } from 'date-fns';

const severityIcon: Record<string, React.ElementType> = {
  critical: ShieldAlert,
  warning: AlertTriangle,
  info: Info,
};

const severityColor: Record<string, string> = {
  critical: 'bg-rose-50 text-rose-700 border-rose-200 dark:bg-rose-950 dark:text-rose-300 dark:border-rose-800',
  warning: 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950 dark:text-amber-300 dark:border-amber-800',
  info: 'bg-sky-50 text-sky-700 border-sky-200 dark:bg-sky-950 dark:text-sky-300 dark:border-sky-800',
};

function AlertCard({ alert, onResolve }: { alert: AdminAlertDTO; onResolve: (id: string) => void }) {
  const Icon = severityIcon[alert.severity] || Info;
  const isResolved = alert.resolved === 'true';

  return (
    <Card className={isResolved ? 'opacity-60' : ''}>
      <CardContent className="p-4">
        <div className="flex items-start gap-3">
          <div className={`p-2 rounded-full mt-0.5 ${isResolved ? 'bg-muted' : severityColor[alert.severity]?.split(' ')[0] || 'bg-muted'}`}>
            <Icon className={`w-4 h-4 ${isResolved ? 'text-muted-foreground' : ''}`} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <h4 className="text-sm font-semibold">{alert.title}</h4>
              {!isResolved && (
                <Badge variant="outline" className="text-xs capitalize">
                  {alert.severity}
                </Badge>
              )}
              {isResolved && (
                <Badge variant="outline" className="text-xs bg-muted text-muted-foreground">
                  Resolved
                </Badge>
              )}
            </div>
            <p className="text-sm text-muted-foreground whitespace-pre-wrap">{alert.message}</p>
            <div className="flex items-center gap-3 mt-2 text-xs text-muted-foreground">
              <span className="flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {format(new Date(alert.timestamp), 'MMM d, yyyy h:mm a')}
              </span>
              {alert.cooldown_until && !isResolved && (
                <span>
                  Cooldown until: {format(new Date(alert.cooldown_until), 'MMM d, h:mm a')} UTC
                </span>
              )}
            </div>
            {!isResolved && (
              <Button
                variant="ghost"
                size="sm"
                className="mt-2 text-xs"
                onClick={() => onResolve(alert.id)}
              >
                <CheckCircle2 className="w-3 h-3 mr-1" />
                Dismiss
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default function AdminAlertsPage() {
  const [alerts, setAlerts] = useState<AdminAlertDTO[]>([]);
  const [total, setTotal] = useState(0);
  const [unresolvedCount, setUnresolvedCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadAlerts = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.alerts.list();
      setAlerts(data.alerts);
      setTotal(data.total);
      setUnresolvedCount(data.unresolved_count);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load alerts');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAlerts();
  }, []);

  const handleResolve = async (alertId: string) => {
    try {
      await api.alerts.resolve(alertId);
      // Optimistic update
      setAlerts((prev) =>
        prev.map((a) => (a.id === alertId ? { ...a, resolved: 'true' } : a)),
      );
      setUnresolvedCount((prev) => Math.max(0, prev - 1));
    } catch (err) {
      console.error('Failed to resolve alert', err);
    }
  };

  return (
    <AdminGuard>
      <AdminShell>
        <div className="space-y-6">
          {/* Header */}
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-2xl font-semibold font-display">System Alerts</h1>
              <p className="text-sm text-muted-foreground mt-1">
                {unresolvedCount > 0
                  ? `${unresolvedCount} unresolved alert${unresolvedCount !== 1 ? 's' : ''}`
                  : 'No unresolved alerts'}
              </p>
            </div>
            <Button variant="outline" size="sm" onClick={loadAlerts} disabled={loading}>
              <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>

          {/* Loading */}
          {loading && (
            <div className="text-center py-12">
              <p className="text-sm text-muted-foreground">Loading alerts…</p>
            </div>
          )}

          {/* Error */}
          {error && !loading && (
            <div className="text-center py-12">
              <p className="text-sm text-destructive mb-2">{error}</p>
              <Button variant="outline" size="sm" onClick={loadAlerts}>
                Retry
              </Button>
            </div>
          )}

          {/* Alert list */}
          {!loading && !error && (
            <>
              {alerts.length === 0 ? (
                <div className="text-center py-16">
                  <CheckCircle2 className="w-12 h-12 text-emerald-500 mx-auto mb-3" />
                  <h3 className="text-lg font-medium">All clear</h3>
                  <p className="text-sm text-muted-foreground">No system alerts to show.</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {alerts.map((alert) => (
                    <AlertCard key={alert.id} alert={alert} onResolve={handleResolve} />
                  ))}
                </div>
              )}
              <Separator />
              <p className="text-xs text-muted-foreground text-center">
                {total} alert{total !== 1 ? 's' : ''} total
              </p>
            </>
          )}
        </div>
      </AdminShell>
    </AdminGuard>
  );
}
