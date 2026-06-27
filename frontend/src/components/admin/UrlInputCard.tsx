'use client';

import { useState } from 'react';
import { Globe, Youtube, Loader2, ExternalLink, AlertCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent } from '@/components/ui/card';
import type { SourceType } from '@/types/source';
import type { ExtractedMetadata } from '@/lib/utils/metadataExtractor';
import { isValidYouTubeUrl, getYouTubeVideoId, getYouTubeThumbnail, extractMetadataFromUrl } from '@/lib/utils/metadataExtractor';

interface UrlInputCardProps {
  sourceType: SourceType;
  onMetadataFetched: (url: string, metadata: ExtractedMetadata) => void;
}

export function UrlInputCard({ sourceType, onMetadataFetched }: UrlInputCardProps) {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [metadata, setMetadata] = useState<ExtractedMetadata | null>(null);
  const [fetchFailed, setFetchFailed] = useState(false);

  const isYouTube = sourceType === 'youtube';
  const placeholder = isYouTube
    ? 'https://www.youtube.com/watch?v=... or https://youtu.be/...'
    : 'https://example.com/article';

  const validateUrl = (value: string): string | null => {
    if (!value.trim()) return 'URL is required';
    try {
      new URL(value);
    } catch {
      return 'Please enter a valid URL';
    }
    if (isYouTube && !isValidYouTubeUrl(value)) {
      return 'Please enter a valid YouTube URL (youtube.com/watch or youtu.be)';
    }
    return null;
  };

  const handleFetch = async () => {
    const validationError = validateUrl(url);
    if (validationError) {
      setError(validationError);
      return;
    }

    setError(null);
    setLoading(true);
    setFetchFailed(false);

    try {
      const data = await extractMetadataFromUrl(url);
      setMetadata(data);
      onMetadataFetched(url, data);
    } catch {
      setFetchFailed(true);
      setMetadata(null);
    } finally {
      setLoading(false);
    }
  };

  const videoId = isYouTube ? getYouTubeVideoId(url) : null;
  const thumbnailUrl = videoId ? getYouTubeThumbnail(videoId) : null;

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-xl font-semibold font-display">
          {isYouTube ? 'Add a YouTube video' : 'Add a webpage'}
        </h2>
        <p className="text-sm text-muted-foreground mt-1">
          {isYouTube
            ? 'Paste a YouTube URL to fetch video metadata and transcript.'
            : 'Paste a webpage URL to scrape content and metadata.'}
        </p>
      </div>

      <div className="space-y-3">
        <div className="space-y-2">
          <Label htmlFor="url-input">URL</Label>
          <div className="flex gap-2">
            <div className="relative flex-1">
              <div className="absolute left-3 top-1/2 -translate-y-1/2">
                {isYouTube ? (
                  <Youtube className="w-4 h-4 text-rose-500" />
                ) : (
                  <Globe className="w-4 h-4 text-green-500" />
                )}
              </div>
              <Input
                id="url-input"
                placeholder={placeholder}
                value={url}
                onChange={(e) => {
                  setUrl(e.target.value);
                  setError(null);
                }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleFetch();
                }}
                className="pl-10"
              />
            </div>
            <Button onClick={handleFetch} disabled={loading}>
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Fetching...
                </>
              ) : (
                'Fetch metadata'
              )}
            </Button>
          </div>
          {error && (
            <p className="text-sm text-destructive flex items-center gap-1">
              <AlertCircle className="w-3 h-3" />
              {error}
            </p>
          )}
        </div>

        {/* YouTube thumbnail preview (before fetch) */}
        {isYouTube && thumbnailUrl && !metadata && (
          <Card className="overflow-hidden">
            <CardContent className="p-0">
              <div className="relative aspect-video bg-muted">
                <img
                  src={thumbnailUrl}
                  alt="YouTube video thumbnail"
                  className="w-full h-full object-cover"
                />
              </div>
            </CardContent>
          </Card>
        )}

        {/* Fetched metadata preview */}
        <AnimatePresence>
          {metadata && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.3 }}
            >
              <Card className="overflow-hidden">
                {metadata.thumbnailUrl && (
                  <div className="aspect-video bg-muted relative">
                    <img
                      src={metadata.thumbnailUrl}
                      alt="Video thumbnail"
                      className="w-full h-full object-cover"
                    />
                  </div>
                )}
                <CardContent className="p-4 space-y-2">
                  <h3 className="font-semibold">{metadata.title}</h3>
                  {metadata.description && (
                    <p className="text-sm text-muted-foreground line-clamp-3">
                      {metadata.description}
                    </p>
                  )}
                  <div className="flex items-center gap-2 flex-wrap">
                    {metadata.authors.length > 0 && (
                      <span className="text-xs text-muted-foreground">
                        By {metadata.authors.join(', ')}
                      </span>
                    )}
                    {metadata.publisher && (
                      <span className="text-xs text-muted-foreground">
                        • {metadata.publisher}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-1 text-xs text-primary">
                    <ExternalLink className="w-3 h-3" />
                    <span className="truncate">{url}</span>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Fetch failed fallback */}
        {fetchFailed && (
          <div className="p-4 rounded-lg border bg-amber-50 border-amber-200">
            <p className="text-sm text-amber-800 font-medium">Could not fetch metadata automatically</p>
            <p className="text-xs text-amber-700 mt-1">
              You can still continue and fill in the metadata manually.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
