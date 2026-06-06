'use client';

import Link from 'next/link';
import {
  Database,
  Loader2,
  AlertTriangle,
  Plus,
  FileText,
  FileCode,
  Mic,
  Globe,
  Youtube,
  ArrowRight,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { AdminShell } from '@/components/layout/AdminShell';
import { AdminGuard } from '@/components/AuthGuard';
import { ProcessingStatus } from '@/components/admin/ProcessingStatus';
import { DashboardCardSkeleton } from '@/components/Skeletons';
import { mockSources } from '@/lib/mockData';
import { SOURCE_TYPE_CONFIG, type SourceType } from '@/types/source';
import { format } from 'date-fns';

const typeIcons: Record<SourceType, React.ElementType> = {
  pdf: FileText,
  text: FileCode,
  audio: Mic,
  webpage: Globe,
  youtube: Youtube,
};

export default function AdminDashboardPage() {
  // Compute stats from mock data
  const totalSources = mockSources.length;
  const processingSources = mockSources.filter((s) => s.status === 'processing' || s.status === 'queued');
  const errorSources = mockSources.filter((s) => s.status === 'error');
  const sourcesByType = Object.entries(SOURCE_TYPE_CONFIG).map(([type, config]) => ({
    type,
    label: config.label,
    count: mockSources.filter((s) => s.type === type).length,
    Icon: typeIcons[type as SourceType],
    color: config.color,
  }));

  // Incomplete metadata = sources missing required fields (title, authors, sensitivity)
  const incompleteMetadata = mockSources.filter(
    (s) => !s.title || s.authors.length === 0 || !s.contentSensitivity
  );

  // Recent additions (sorted by createdAt desc)
  const recentSources = [...mockSources]
    .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
    .slice(0, 5);

  // Flagged for attention (error status or incomplete)
  const flaggedSources = [
    ...errorSources,
    ...incompleteMetadata.filter((s) => s.status !== 'error'),
  ];

  return (
    <AdminGuard>
    <AdminShell>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-semibold font-display">Dashboard</h1>
            <p className="text-sm text-muted-foreground mt-1">
              Overview of your knowledge base
            </p>
          </div>
          <Button asChild>
            <Link href="/admin/sources/new">
              <Plus className="w-4 h-4 mr-2" />
              Add source
            </Link>
          </Button>
        </div>

        {/* Stat cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardDescription className="flex items-center gap-2">
                <Database className="w-4 h-4" />
                Total Sources
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold">{totalSources}</p>
              <p className="text-xs text-muted-foreground mt-1">
                Across all source types
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardDescription className="flex items-center gap-2">
                <Database className="w-4 h-4" />
                Sources by Type
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-1.5">
                {sourcesByType
                  .filter((t) => t.count > 0)
                  .map((t) => (
                    <div key={t.type} className="flex items-center justify-between text-sm">
                      <span className="flex items-center gap-1.5">
                        <t.Icon className={`w-3.5 h-3.5 ${t.color}`} />
                        {t.label}
                      </span>
                      <span className="font-medium">{t.count}</span>
                    </div>
                  ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardDescription className="flex items-center gap-2">
                <Loader2 className="w-4 h-4" />
                Processing
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold text-amber-600">{processingSources.length}</p>
              <p className="text-xs text-muted-foreground mt-1">
                {errorSources.length > 0 && (
                  <span className="text-rose-600">{errorSources.length} with errors</span>
                )}
                {errorSources.length === 0 && 'No errors'}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardDescription className="flex items-center gap-2">
                <AlertTriangle className="w-4 h-4" />
                Incomplete Metadata
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold">{incompleteMetadata.length}</p>
              <p className="text-xs text-muted-foreground mt-1">
                Sources needing attention
              </p>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Recent additions */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Recent additions</CardTitle>
              <CardDescription>Last 5 sources added</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {recentSources.map((source) => {
                const TypeIcon = typeIcons[source.type];
                const typeConfig = SOURCE_TYPE_CONFIG[source.type];
                return (
                  <Link
                    key={source.id}
                    href={`/admin/sources/${source.id}`}
                    className="flex items-center gap-3 p-2 rounded-lg hover:bg-muted/50 transition-colors"
                  >
                    <TypeIcon className={`w-4 h-4 flex-shrink-0 ${typeConfig.color}`} />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{source.title}</p>
                      <p className="text-xs text-muted-foreground">
                        {format(new Date(source.createdAt), 'MMM d, yyyy')}
                      </p>
                    </div>
                    <ProcessingStatus
                      status={source.status}
                      indexedAt={source.indexedAt}
                      errorMessage={source.errorMessage}
                    />
                  </Link>
                );
              })}
              <Separator />
              <Button variant="ghost" size="sm" className="w-full" asChild>
                <Link href="/admin/sources" className="flex items-center justify-center gap-1">
                  View all sources <ArrowRight className="w-3 h-3" />
                </Link>
              </Button>
            </CardContent>
          </Card>

          {/* Flagged for attention */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Needs attention</CardTitle>
              <CardDescription>Sources with errors or incomplete metadata</CardDescription>
            </CardHeader>
            <CardContent>
              {flaggedSources.length === 0 ? (
                <div className="flex flex-col items-center py-8 text-center">
                  <div className="w-12 h-12 rounded-full bg-emerald-50 flex items-center justify-center mb-3">
                    <FileText className="w-6 h-6 text-emerald-500" />
                  </div>
                  <p className="text-sm text-muted-foreground">All sources are in good shape!</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {flaggedSources.map((source) => {
                    const TypeIcon = typeIcons[source.type];
                    const typeConfig = SOURCE_TYPE_CONFIG[source.type];
                    const isError = source.status === 'error';
                    return (
                      <Link
                        key={source.id}
                        href={`/admin/sources/${source.id}`}
                        className="flex items-center gap-3 p-2 rounded-lg hover:bg-muted/50 transition-colors"
                      >
                        <TypeIcon className={`w-4 h-4 flex-shrink-0 ${typeConfig.color}`} />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium truncate">{source.title}</p>
                          <p className="text-xs text-muted-foreground">
                            {isError
                              ? source.errorMessage?.slice(0, 60)
                              : 'Missing required metadata fields'}
                          </p>
                        </div>
                        <Badge
                          variant="outline"
                          className={
                            isError
                              ? 'bg-rose-50 text-rose-700 border-rose-200'
                              : 'bg-amber-50 text-amber-700 border-amber-200'
                          }
                        >
                          {isError ? 'Error' : 'Incomplete'}
                        </Badge>
                      </Link>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </AdminShell>
    </AdminGuard>
  );
}
