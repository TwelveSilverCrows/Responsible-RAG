'use client';

import { Clock, Loader2, CheckCircle, XCircle } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import type { SourceStatus } from '@/types/source';
import { format } from 'date-fns';

interface ProcessingStatusProps {
  status: SourceStatus;
  indexedAt?: string | null;
  errorMessage?: string | null;
  onRetry?: () => void;
}

const statusConfig = {
  queued: {
    icon: Clock,
    label: 'Queued',
    badgeClass: 'bg-gray-100 text-gray-600 border-gray-200',
    iconClass: 'text-gray-400',
  },
  processing: {
    icon: Loader2,
    label: 'Indexing...',
    badgeClass: 'bg-amber-50 text-amber-700 border-amber-200',
    iconClass: 'text-amber-500 animate-spin',
  },
  indexed: {
    icon: CheckCircle,
    label: 'Indexed',
    badgeClass: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    iconClass: 'text-emerald-500',
  },
  error: {
    icon: XCircle,
    label: 'Error',
    badgeClass: 'bg-rose-50 text-rose-700 border-rose-200',
    iconClass: 'text-rose-500',
  },
} as const;

export function ProcessingStatus({
  status,
  indexedAt,
  errorMessage,
  onRetry,
}: ProcessingStatusProps) {
  const config = statusConfig[status];
  const Icon = config.icon;

  // TanStack Query refetchInterval could be used here for polling:
  // const { data } = useQuery({ queryKey: ['source-status'], refetchInterval: status === 'processing' ? 3000 : false })

  return (
    <div className="flex items-center gap-2">
      <Badge variant="outline" className={config.badgeClass}>
        <Icon className={`w-3 h-3 ${config.iconClass}`} />
        <span>{config.label}</span>
      </Badge>
      {status === 'indexed' && indexedAt && (
        <span className="text-xs text-muted-foreground">
          {format(new Date(indexedAt), 'MMM d, yyyy h:mm a')}
        </span>
      )}
      {status === 'error' && errorMessage && (
        <span className="text-xs text-rose-600 max-w-[200px] truncate" title={errorMessage}>
          {errorMessage}
        </span>
      )}
      {status === 'error' && onRetry && (
        <Button variant="ghost" size="sm" className="h-6 text-xs" onClick={onRetry}>
          Retry
        </Button>
      )}
    </div>
  );
}
