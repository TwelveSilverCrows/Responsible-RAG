'use client';

import { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  ArrowLeft,
  Pencil,
  Trash2,
  FileText,
  FileCode,
  Mic,
  Globe,
  Youtube,
  ExternalLink,
  Clock,
  Play,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
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
import { AdminShell } from '@/components/layout/AdminShell';
import { AdminGuard } from '@/components/AuthGuard';
import { ProcessingStatus } from '@/components/admin/ProcessingStatus';
import { MetadataForm } from '@/components/admin/MetadataForm';
import { getSourceById, mockProcessingLogs } from '@/lib/mockData';
import { SOURCE_TYPE_CONFIG, type SourceType } from '@/types/source';
import { getYouTubeEmbedUrl, getYouTubeVideoId } from '@/lib/utils/metadataExtractor';
import { format } from 'date-fns';
import { cn } from '@/lib/utils';

const typeIcons: Record<SourceType, React.ElementType> = {
  pdf: FileText,
  text: FileCode,
  audio: Mic,
  webpage: Globe,
  youtube: Youtube,
};

export default function SourceDetailPage() {
  const params = useParams();
  const navigate = useNavigate();
  const id = params.id as string;
  const source = getSourceById(id);
  const [editMode, setEditMode] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

  if (!source) {
    return (
      <AdminGuard>
      <AdminShell>
        <div className="flex flex-col items-center justify-center min-h-[50vh] text-center">
          <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4">
            <FileText className="w-8 h-8 text-muted-foreground" />
          </div>
          <h2 className="text-xl font-semibold mb-2">Source not found</h2>
          <p className="text-sm text-muted-foreground mb-4">
            The source you&apos;re looking for doesn&apos;t exist or has been removed.
          </p>
          <Button asChild variant="outline">
            <Link to="/admin/sources">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Sources
            </Link>
          </Button>
        </div>
      </AdminShell>
      </AdminGuard>
    );
  }

  const TypeIcon = typeIcons[source.type];
  const typeConfig = SOURCE_TYPE_CONFIG[source.type];
  const processingLogs = mockProcessingLogs[source.id] ?? [];

  const videoId = source.type === 'youtube' && source.url ? getYouTubeVideoId(source.url) : null;
  const embedUrl = videoId ? getYouTubeEmbedUrl(videoId) : null;

  const metadataItems = [
    { label: 'Title', value: source.title },
    { label: 'Type', value: typeConfig.label },
    { label: 'Authors', value: source.authors.join(', ') },
    {
      label: 'Publication Date',
      value: source.publicationDate
        ? format(new Date(source.publicationDate), 'MMMM d, yyyy')
        : '—',
    },
    { label: 'Publisher', value: source.publisher || '—' },
    { label: 'URL', value: source.url || '—' },
    { label: 'DOI', value: source.doi || '—' },
    { label: 'Language', value: source.language?.toUpperCase() || '—' },
    { label: 'Description', value: source.description || '—' },
    { label: 'Tags', value: source.tags.length > 0 ? source.tags.join(', ') : '—' },
    {
      label: 'Sensitivity',
      value: source.contentSensitivity.charAt(0).toUpperCase() + source.contentSensitivity.slice(1),
    },
    { label: 'Internal Notes', value: source.internalNotes || '—' },
    {
      label: 'Date Added',
      value: format(new Date(source.createdAt), 'MMMM d, yyyy h:mm a'),
    },
    {
      label: 'Last Updated',
      value: format(new Date(source.updatedAt), 'MMMM d, yyyy h:mm a'),
    },
  ];

  return (
    <AdminGuard>
    <AdminShell>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-3">
            <Button variant="ghost" size="icon" className="flex-shrink-0" asChild>
              <Link to="/admin/sources" aria-label="Back to sources">
                <ArrowLeft className="w-5 h-5" />
              </Link>
            </Button>
            <div>
              <div className="flex items-center gap-2 mb-1">
                <TypeIcon className={`w-5 h-5 ${typeConfig.color}`} />
                <Badge variant="secondary" className="text-xs">
                  {typeConfig.label}
                </Badge>
              </div>
              <h1 className="text-2xl font-semibold font-display">{source.title}</h1>
            </div>
          </div>
          <div className="flex items-center gap-2 flex-shrink-0">
            <Button
              variant="outline"
              onClick={() => setEditMode(!editMode)}
            >
              <Pencil className="w-4 h-4 mr-2" />
              {editMode ? 'Cancel' : 'Edit'}
            </Button>
            <Button
              variant="destructive"
              onClick={() => setDeleteDialogOpen(true)}
            >
              <Trash2 className="w-4 h-4 mr-2" />
              Delete
            </Button>
          </div>
        </div>

        {/* Status bar */}
        <div className="flex items-center gap-4">
          <ProcessingStatus
            status={source.status}
            indexedAt={source.indexedAt}
            errorMessage={source.errorMessage}
          />
        </div>

        {/* Edit mode */}
        {editMode ? (
          <MetadataForm
            sourceType={source.type}
            initialData={{
              title: source.title,
              authors: source.authors,
              publicationDate: source.publicationDate,
              publisher: source.publisher,
              url: source.url,
              doi: source.doi,
              language: source.language,
              description: source.description,
              tags: source.tags,
              contentSensitivity: source.contentSensitivity,
              internalNotes: source.internalNotes,
            }}
            onSubmit={() => {
              setEditMode(false);
            }}
          />
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Source preview */}
            <div className="lg:col-span-1">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Preview</CardTitle>
                </CardHeader>
                <CardContent>
                  {source.type === 'pdf' && (
                    <div className="aspect-[3/4] rounded-lg border bg-muted flex flex-col items-center justify-center p-4 text-center">
                      <FileText className="w-12 h-12 text-red-400 mb-3" />
                      <p className="text-sm font-medium">PDF Preview</p>
                      <p className="text-xs text-muted-foreground mt-1">
                        Document preview would render here
                      </p>
                    </div>
                  )}
                  {source.type === 'youtube' && embedUrl && (
                    <div className="aspect-video rounded-lg overflow-hidden border bg-black">
                      <iframe
                        src={embedUrl}
                        title={source.title}
                        className="w-full h-full"
                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                        allowFullScreen
                      />
                    </div>
                  )}
                  {source.type === 'youtube' && !embedUrl && (
                    <div className="aspect-video rounded-lg border bg-muted flex items-center justify-center">
                      <Youtube className="w-12 h-12 text-rose-400" />
                    </div>
                  )}
                  {source.type === 'text' && (
                    <div className="rounded-lg border bg-muted p-4 font-mono text-xs text-muted-foreground space-y-1 max-h-64 overflow-y-auto">
                      <p>{'{ Markdown / Text content preview }'}</p>
                      <p className="text-foreground/60">
                        # {source.title}
                      </p>
                      <p className="text-foreground/40">
                        Content preview would render here with syntax highlighting...
                      </p>
                    </div>
                  )}
                  {source.type === 'audio' && (
                    <div className="rounded-lg border bg-muted p-6 flex flex-col items-center gap-4">
                      <div className="w-16 h-16 rounded-full bg-purple-100 flex items-center justify-center">
                        <Play className="w-8 h-8 text-purple-600 ml-1" />
                      </div>
                      <div className="w-full h-2 bg-purple-100 rounded-full">
                        <div className="w-1/3 h-full bg-purple-500 rounded-full" />
                      </div>
                      <p className="text-xs text-muted-foreground">Audio player placeholder</p>
                    </div>
                  )}
                  {source.type === 'webpage' && source.url && (
                    <div className="rounded-lg border bg-muted p-4 text-center">
                      <Globe className="w-10 h-10 text-green-400 mx-auto mb-3" />
                      <p className="text-sm font-medium mb-2">Webpage</p>
                      <a
                        href={source.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-sm text-primary hover:underline"
                      >
                        <ExternalLink className="w-3 h-3" />
                        Open in new tab
                      </a>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* Metadata */}
            <div className="lg:col-span-2">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Metadata</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-4">
                    {metadataItems.map((item) => (
                      <div
                        key={item.label}
                        className={cn(
                          'space-y-1',
                          item.label === 'Description' || item.label === 'Internal Notes'
                            ? 'sm:col-span-2'
                            : ''
                        )}
                      >
                        <dt className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                          {item.label}
                        </dt>
                        <dd className="text-sm">
                          {item.label === 'Tags' && source.tags.length > 0 ? (
                            <div className="flex flex-wrap gap-1">
                              {source.tags.map((tag) => (
                                <Badge key={tag} variant="secondary" className="text-xs">
                                  {tag}
                                </Badge>
                              ))}
                            </div>
                          ) : item.label === 'Sensitivity' ? (
                            <Badge
                              variant="outline"
                              className={
                                source.contentSensitivity === 'high'
                                  ? 'bg-rose-50 text-rose-700 border-rose-200'
                                  : source.contentSensitivity === 'medium'
                                    ? 'bg-amber-50 text-amber-700 border-amber-200'
                                    : 'bg-emerald-50 text-emerald-700 border-emerald-200'
                              }
                            >
                              {item.value}
                            </Badge>
                          ) : item.label === 'URL' && source.url ? (
                            <a
                              href={source.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-primary hover:underline inline-flex items-center gap-1"
                            >
                              {source.url} <ExternalLink className="w-3 h-3" />
                            </a>
                          ) : (
                            <span>{item.value}</span>
                          )}
                        </dd>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Processing log */}
              <Card className="mt-6">
                <CardHeader>
                  <CardTitle className="text-base flex items-center gap-2">
                    <Clock className="w-4 h-4" />
                    Processing Log
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {processingLogs.length === 0 ? (
                    <p className="text-sm text-muted-foreground">No processing logs available.</p>
                  ) : (
                    <div className="space-y-3">
                      {processingLogs.map((log, i) => (
                        <div key={i} className="flex items-start gap-3">
                          <div className="w-2 h-2 rounded-full bg-primary mt-1.5 flex-shrink-0" />
                          <div className="flex-1 min-w-0">
                            <p className="text-sm">{log.message}</p>
                            <p className="text-xs text-muted-foreground">
                              {format(new Date(log.timestamp), 'MMM d, yyyy h:mm:ss a')}
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </div>
        )}

        {/* Delete confirmation dialog */}
        <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Delete this source?</AlertDialogTitle>
              <AlertDialogDescription>
                This will remove &ldquo;{source.title}&rdquo; from the knowledge base. This cannot
                be undone.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction
                onClick={() => {
                  setDeleteDialogOpen(false);
                  navigate('/admin/sources');
                }}
                className="bg-destructive text-white hover:bg-destructive/90"
              >
                Delete
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>
    </AdminShell>
    </AdminGuard>
  );
}
