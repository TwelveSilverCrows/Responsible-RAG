'use client';

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
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
import { DashboardCardSkeleton } from '@/components/Skeletons';
import { api, type SourceResponseDTO, type StatsResponseDTO } from '@/lib/api';
import { SOURCE_TYPE_CONFIG, type SourceType } from '@/types/source';
import { format } from 'date-fns';

const typeIcons: Record<string, React.ElementType> = {
  pdf: FileText,
  text: FileCode,
  audio: Mic,
  webpage: Globe,
  youtube: Youtube,
};

export default function AdminDashboardPage() {
  const [stats, setStats] = useState<StatsResponseDTO | null>(null);
  const [recentSources, setRecentSources] = useState<SourceResponseDTO[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const [statsData, sourcesData] = await Promise.all([
          api.sources.stats(),
          api.sources.list(1, 5),
        ]);
        setStats(statsData);
        setRecentSources(sourcesData.sources);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load dashboard');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  // Derive sources-by-type breakdown from recent sources (best we can do
  // without a dedicated endpoint — the full list is available on the Sources page).
  const indexedSources = recentSources.filter((s) => s.status === 'indexed');
  const sourcesByType = indexedSources.length > 0
    ? Object.entries(SOURCE_TYPE_CONFIG)
        .map(([type, config]) => ({
          type,
          label: config.label,
          count: indexedSources.filter((s) => s.source_type === type).length,
          Icon: typeIcons[type],
          color: config.color,
        }))
        .filter((t) => t.count > 0)
    : [];

  // Flagged from the recent list
  const flaggedSources = recentSources.filter(
    (s) => s.status === 'error' || !s.title || s.authors.length === 0 || !s.content_sensitivity,
  );

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
            <Link to="/admin/sources/new">
              <Plus className="w-4 h-4 mr-2" />
              Add source
            </Link>
          </Button>
        </div>

        {/* Loading state */}
        {loading && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <DashboardCardSkeleton key={i} />
            ))}
          </div>
        )}

        {/* Error state */}
        {error && !loading && (
          <div className="text-center py-12">
            <p className="text-sm text-destructive mb-2">{error}</p>
            <Button variant="outline" size="sm" onClick={() => window.location.reload()}>
              Retry
            </Button>
          </div>
        )}

        {/* Data loaded */}
        {!loading && !error && stats && (
          <>
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
                  <p className="text-3xl font-bold">{stats.total_sources}</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {stats.indexed_sources} indexed
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
                  {sourcesByType.length > 0 ? (
                    <div className="space-y-1.5">
                      {sourcesByType.map((t) => (
                        <div key={t.type} className="flex items-center justify-between text-sm">
                          <span className="flex items-center gap-1.5">
                            <t.Icon className={`w-3.5 h-3.5 ${t.color}`} />
                            {t.label}
                          </span>
                          <span className="font-medium">{t.count}</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">—</p>
                  )}
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
                  <p className="text-3xl font-bold text-amber-600">{stats.processing_sources}</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {stats.error_sources > 0 ? (
                      <span className="text-rose-600">{stats.error_sources} with errors</span>
                    ) : (
                      'No errors'
                    )}
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
                  <p className="text-3xl font-bold">{stats.incomplete_metadata}</p>
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
                    const TypeIcon = typeIcons[source.source_type] || FileText;
                    const typeConfig = SOURCE_TYPE_CONFIG[source.source_type as SourceType];
                    return (
                      <Link
                        key={source.id}
                        to={`/admin/sources/${source.id}`}
                        className="flex items-center gap-3 p-2 rounded-lg hover:bg-muted/50 transition-colors"
                      >
                        <TypeIcon className={`w-4 h-4 flex-shrink-0 ${typeConfig?.color || ''}`} />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium truncate">{source.title}</p>
                          <p className="text-xs text-muted-foreground">
                            {source.source_type}
                          </p>
                        </div>
                        <Badge variant="outline" className="text-xs">
                          {source.chunk_count} chunk{source.chunk_count !== 1 ? 's' : ''}
                        </Badge>
                      </Link>
                    );
                  })}
                  {recentSources.length === 0 && (
                    <p className="text-sm text-muted-foreground py-4 text-center">No sources yet.</p>
                  )}
                  <Separator />
                  <Button variant="ghost" size="sm" className="w-full" asChild>
                    <Link to="/admin/sources" className="flex items-center justify-center gap-1">
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
                        const TypeIcon = typeIcons[source.source_type] || FileText;
                        const typeConfig = SOURCE_TYPE_CONFIG[source.source_type as SourceType];
                        const isError = source.status === 'error';
                        return (
                          <Link
                            key={source.id}
                            to={`/admin/sources/${source.id}`}
                            className="flex items-center gap-3 p-2 rounded-lg hover:bg-muted/50 transition-colors"
                          >
                            <TypeIcon className={`w-4 h-4 flex-shrink-0 ${typeConfig?.color || ''}`} />
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-medium truncate">{source.title}</p>
                              <p className="text-xs text-muted-foreground">
                                {isError
                                  ? source.error_message?.slice(0, 60)
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
          </>
        )}
      </div>
    </AdminShell>
    </AdminGuard>
  );
}
