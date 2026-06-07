'use client';

import { Link } from 'react-router-dom';
import { Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { AdminShell } from '@/components/layout/AdminShell';
import { AdminGuard } from '@/components/AuthGuard';
import { SourceTable } from '@/components/admin/SourceTable';
import { mockSources } from '@/lib/mockData';

export default function SourcesLibraryPage() {
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

        {/* Source table */}
        <SourceTable sources={mockSources} />
      </div>
    </AdminShell>
    </AdminGuard>
  );
}
