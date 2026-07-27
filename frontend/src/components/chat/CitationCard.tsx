'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FileText,
  FileCode,
  Mic,
  Globe,
  Youtube,
  ChevronDown,
  ExternalLink,
} from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import type { Citation } from '@/types/chat';
import type { SourceType } from '@/types/source';
import { cn } from '@/lib/utils';

const sourceTypeIcon: Record<SourceType, React.ElementType> = {
  pdf: FileText,
  text: FileCode,
  audio: Mic,
  webpage: Globe,
  youtube: Youtube,
};

function getYear(date: string | null): string {
  if (!date) return '';
  return new Date(date).getFullYear().toString();
}

export function CitationCard({ citation }: { citation: Citation }) {
  const [expanded, setExpanded] = useState(false);
  const Icon = sourceTypeIcon[citation.source.type] ?? FileText;

  return (
    <Card className="py-0 gap-0 overflow-hidden border border-border/60">
      <button
        onClick={() => setExpanded(!expanded)}
        aria-expanded={expanded}
        aria-label={`Citation ${citation.number}: ${citation.source.title}`}
        className="w-full text-left"
      >
        <CardContent className="p-3 flex items-start gap-2.5">
          <span className="flex-shrink-0 w-5 h-5 rounded-full bg-primary/10 text-primary text-xs font-semibold flex items-center justify-center mt-0.5">
            {citation.number}
          </span>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium leading-snug truncate">
              {citation.source.title}
            </p>
            <p className="text-xs text-muted-foreground mt-0.5 truncate">
              {citation.source.authors.join(', ')}
              {citation.source.publicationDate && ` · ${getYear(citation.source.publicationDate)}`}
            </p>
          </div>
          <div className="flex items-center gap-1 flex-shrink-0 mt-0.5">
            <Icon className="w-3.5 h-3.5 text-muted-foreground" />
            <ChevronDown
              className={cn(
                'w-3.5 h-3.5 text-muted-foreground transition-transform duration-200',
                expanded && 'rotate-180'
              )}
            />
          </div>
        </CardContent>
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="px-3 pb-3 pt-0 space-y-2 border-t border-border/40">
              {/* Excerpt */}
              <blockquote className="mt-2 pl-3 border-l-2 border-primary/40 text-xs text-muted-foreground italic leading-relaxed">
                &ldquo;{citation.excerpt}&rdquo;
              </blockquote>

              {/* Full metadata */}
              <div className="text-xs text-muted-foreground space-y-0.5">
                {citation.source.publisher && (
                  <p>
                    <span className="font-medium text-foreground/70">Publisher:</span>{' '}
                    {citation.source.publisher}
                  </p>
                )}
                {citation.source.doi && (
                  <p>
                    <span className="font-medium text-foreground/70">DOI:</span>{' '}
                    {citation.source.doi}
                  </p>
                )}
                {citation.source.tags.length > 0 && (
                  <p>
                    <span className="font-medium text-foreground/70">Tags:</span>{' '}
                    {citation.source.tags.join(', ')}
                  </p>
                )}
              </div>

              {/* View source link */}
              {citation.source.url && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 text-xs text-primary gap-1 px-0 hover:bg-transparent"
                  asChild
                  onClick={(e) => e.stopPropagation()}
                >
                  <a
                    href={citation.source.url}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    View source <ExternalLink className="w-3 h-3" />
                  </a>
                </Button>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </Card>
  );
}

interface CitationListProps {
  citations: Citation[];
  maxVisible?: number;
}

export function CitationList({ citations, maxVisible = 5 }: CitationListProps) {
  const [showAll, setShowAll] = useState(false);
  const visible = showAll ? citations : citations.slice(0, maxVisible);
  const hiddenCount = citations.length - maxVisible;

  if (citations.length === 0) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: 0.1 }}
      className="space-y-2 mt-3"
    >
      <p className="text-xs font-medium text-muted-foreground">Sources</p>
      <div className="space-y-1.5">
        {visible.map((citation) => (
          <CitationCard key={citation.id} citation={citation} />
        ))}
      </div>
      {hiddenCount > 0 && !showAll && (
        <button
          onClick={() => setShowAll(true)}
          className="text-xs text-primary hover:underline cursor-pointer"
        >
          Show {hiddenCount} more {hiddenCount === 1 ? 'source' : 'sources'}
        </button>
      )}
      {showAll && hiddenCount > 0 && (
        <button
          onClick={() => setShowAll(false)}
          className="text-xs text-primary hover:underline cursor-pointer"
        >
          Show fewer
        </button>
      )}
    </motion.div>
  );
}
