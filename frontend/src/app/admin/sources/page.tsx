'use client';

import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { Plus, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { AdminShell } from '@/components/layout/AdminShell';
import { AdminGuard } from '@/components/AuthGuard';
import { SourceTable } from '@/components/admin/SourceTable';
import { api, type SourceResponseDTO } from '@/lib/api';

export default function SourcesLibraryPage() {
  const [sources, setSources] = useState<SourceResponseDTO[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  async function loadSources() {
    setError(null);
    try {
      const data = await api.sources.list();
      setSources(data.sources);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load sources');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadSources();
    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, []);

  // Poll while any source is processing
  useEffect(() => {
    const hasProcessing = sources.some((s) => s.status === 'processing');
    if (hasProcessing && !pollingRef.current) {
      pollingRef.current = setInterval(loadSources, 3000);
    } else if (!hasProcessing && pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
  }, [sources]);

  return (
    <AdminGuard>
    <AdminShell>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-semibold font-display">Sources</h1>
            <p className="text-sm text-muted-foreground mt-1">
              Manage your knowledge base sources
            </p>
          </div>
          <Button asChild>
            <Link to="/admin/sources/new">
              <Plus className="w-4 h-4 mr-2" />
              Add Source
            </Link>
          </Button>
        </div>

        {/* Loading state */}
        {loading && (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
            <span className="ml-2 text-sm text-muted-foreground">Loading sources…</span>
          </div>
        )}

        {/* Error state */}
        {error && !loading && (
          <div className="text-center py-12">
            <p className="text-sm text-destructive mb-2">{error}</p>
            <Button variant="outline" size="sm" onClick={loadSources}>
              Retry
            </Button>
          </div>
        )}

        {/* Source table */}
        {!loading && !error && (
          <SourceTable
            sources={sources.map(s => ({
              id: s.id,
              title: s.title,
              type: s.source_type as any,
              authors: s.authors,
              publicationDate: s.publication_date,
              publisher: s.publisher,
              url: s.url,
              doi: s.doi,
              language: s.language,
              description: s.description,
              tags: s.tags,
              contentSensitivity: s.content_sensitivity as any,
              internalNotes: s.internal_notes,
              status: s.status,
              errorMessage: s.error_message,
              chunkCount: s.chunk_count,
            }))}
            onRefresh={loadSources}
          />
        )}
      </div>
    </AdminShell>
    </AdminGuard>
  );
}
