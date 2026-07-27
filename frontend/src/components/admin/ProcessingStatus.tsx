'use client';

import { Loader2, CheckCircle, XCircle } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import type { SourceStatus } from '@/types/source';

interface ProcessingStatusProps {
  status: SourceStatus;
  errorMessage?: string | null;
}

const statusConfig: Record<SourceStatus, {
  icon: React.ElementType; label: string; className: string; iconClass: string;
}> = {
  processing: {
    icon: Loader2,
    label: 'Processing…',
    className: 'bg-amber-50 text-amber-700 border-amber-200',
    iconClass: 'text-amber-500 animate-spin',
  },
  indexed: {
    icon: CheckCircle,
    label: 'Indexed',
    className: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    iconClass: 'text-emerald-500',
  },
  error: {
    icon: XCircle,
    label: 'Error',
    className: 'bg-rose-50 text-rose-700 border-rose-200',
    iconClass: 'text-rose-500',
  },
};

export function ProcessingStatus({ status, errorMessage }: ProcessingStatusProps) {
  const config = statusConfig[status];
  const Icon = config.icon || CheckCircle;

  return (
    <div className="flex items-center gap-2">
      <Badge variant="outline" className={config.className}>
        <Icon className={`w-3 h-3 ${config.iconClass}`} />
        <span>{config.label}</span>
      </Badge>
      {status === 'error' && errorMessage && (
        <span className="text-xs text-rose-600 max-w-[200px] truncate" title={errorMessage}>
          {errorMessage}
        </span>
      )}
    </div>
  );
}
