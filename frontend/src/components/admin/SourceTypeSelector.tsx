'use client';

import { FileText, FileCode, Mic, Globe, Youtube } from 'lucide-react';
import { motion } from 'framer-motion';
import { Card, CardContent } from '@/components/ui/card';
import { cn } from '@/lib/utils';
import type { SourceType } from '@/types/source';
import { SOURCE_TYPE_CONFIG } from '@/types/source';

const typeIcons: Record<SourceType, React.ElementType> = {
  pdf: FileText,
  text: FileCode,
  audio: Mic,
  webpage: Globe,
  youtube: Youtube,
};

const accentColors: Record<SourceType, string> = {
  pdf: 'bg-red-50 border-red-200 hover:border-red-400 data-[selected=true]:border-red-500 data-[selected=true]:ring-red-500/20',
  text: 'bg-blue-50 border-blue-200 hover:border-blue-400 data-[selected=true]:border-blue-500 data-[selected=true]:ring-blue-500/20',
  audio: 'bg-purple-50 border-purple-200 hover:border-purple-400 data-[selected=true]:border-purple-500 data-[selected=true]:ring-purple-500/20',
  webpage: 'bg-green-50 border-green-200 hover:border-green-400 data-[selected=true]:border-green-500 data-[selected=true]:ring-green-500/20',
  youtube: 'bg-rose-50 border-rose-200 hover:border-rose-400 data-[selected=true]:border-rose-500 data-[selected=true]:ring-rose-500/20',
};

const iconBgColors: Record<SourceType, string> = {
  pdf: 'bg-red-100 text-red-600',
  text: 'bg-blue-100 text-blue-600',
  audio: 'bg-purple-100 text-purple-600',
  webpage: 'bg-green-100 text-green-600',
  youtube: 'bg-rose-100 text-rose-600',
};

interface SourceTypeSelectorProps {
  value: SourceType | null;
  onChange: (type: SourceType) => void;
}

const sourceTypes: SourceType[] = ['pdf', 'text', 'audio', 'webpage', 'youtube'];

export function SourceTypeSelector({ value, onChange }: SourceTypeSelectorProps) {
  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-xl font-semibold font-display">Choose source type</h2>
        <p className="text-sm text-muted-foreground mt-1">
          Select the type of content you want to add to the knowledge base.
        </p>
      </div>
      <div
        className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4"
        role="radiogroup"
        aria-label="Source type selection"
      >
        {sourceTypes.map((type) => {
          const Icon = typeIcons[type];
          const config = SOURCE_TYPE_CONFIG[type];
          const isSelected = value === type;

          return (
            <motion.div
              key={type}
              whileHover={{ y: -3 }}
              whileTap={{ scale: 0.97 }}
              transition={{ duration: 0.15 }}
            >
              <Card
                role="radio"
                aria-checked={isSelected}
                aria-label={config.label}
                tabIndex={0}
                data-selected={isSelected}
                className={cn(
                  'cursor-pointer transition-all border-2',
                  accentColors[type],
                  isSelected && 'ring-2 ring-offset-2'
                )}
                onClick={() => onChange(type)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    onChange(type);
                  }
                }}
              >
                <CardContent className="flex flex-col items-center gap-3 p-5 text-center">
                  <div
                    className={cn(
                      'w-14 h-14 rounded-xl flex items-center justify-center',
                      iconBgColors[type]
                    )}
                  >
                    <Icon className="w-7 h-7" />
                  </div>
                  <div>
                    <p className="font-semibold text-sm">{config.label}</p>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
