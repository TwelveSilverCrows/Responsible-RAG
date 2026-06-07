'use client';

import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { FileText, FileCode, Mic, Globe, Youtube } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ProcessingStatus } from '@/components/admin/ProcessingStatus';
import type { Source, SourceType } from '@/types/source';
import { SOURCE_TYPE_CONFIG } from '@/types/source';
import { format } from 'date-fns';

const typeIcons: Record<SourceType, React.ElementType> = {
  pdf: FileText,
  text: FileCode,
  audio: Mic,
  webpage: Globe,
  youtube: Youtube,
};

interface SourceCardProps {
  source: Source;
}

export function SourceCard({ source }: SourceCardProps) {
  const navigate = useNavigate();
  const TypeIcon = typeIcons[source.type];
  const typeConfig = SOURCE_TYPE_CONFIG[source.type];

  return (
    <motion.div
      whileHover={{ y: -2, boxShadow: '0 4px 12px rgba(0,0,0,0.08)' }}
      transition={{ duration: 0.2 }}
    >
      <Card
        className="cursor-pointer hover:border-primary/30 transition-colors"
        onClick={() => navigate(`/admin/sources/${source.id}`)}
      >
        <CardContent className="p-4 space-y-3">
          <div className="flex items-start gap-3">
            <div
              className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 bg-muted`}
            >
              <TypeIcon className={`w-5 h-5 ${typeConfig.color}`} />
            </div>
            <div className="min-w-0 flex-1">
              <h3 className="font-semibold text-sm line-clamp-2 leading-tight">
                {source.title}
              </h3>
            </div>
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            <Badge variant="secondary" className="text-xs">
              {typeConfig.label}
            </Badge>
            <ProcessingStatus
              status={source.status}
              indexedAt={source.indexedAt}
              errorMessage={source.errorMessage}
            />
          </div>

          <div className="text-xs text-muted-foreground space-y-1">
            <p className="truncate">
              {source.authors.join(', ')}
            </p>
            <p>
              {source.publicationDate
                ? format(new Date(source.publicationDate), 'MMM d, yyyy')
                : 'No date'}
            </p>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
