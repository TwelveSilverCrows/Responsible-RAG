'use client';

import { useState, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { X, Info, Sparkles } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { Separator } from '@/components/ui/separator';
import type { SourceType, ContentSensitivity } from '@/types/source';
import { SOURCE_TYPE_CONFIG, SENSITIVITY_OPTIONS } from '@/types/source';
import type { SourceMetadataFormData } from '@/lib/schemas/source.schema';
import { sourceMetadataSchema } from '@/lib/schemas/source.schema';

interface MetadataFormProps {
  sourceType: SourceType;
  initialData?: Partial<SourceMetadataFormData>;
  onSubmit: (data: SourceMetadataFormData) => void;
  disabled?: boolean;
}

// Tag/chip input component
function ChipInput({
  value,
  onChange,
  placeholder,
  autoDetected = false,
  onEdit,
}: {
  value: string[];
  onChange: (v: string[]) => void;
  placeholder: string;
  autoDetected?: boolean;
  onEdit?: () => void;
}) {
  const [input, setInput] = useState('');

  const add = () => {
    const trimmed = input.trim();
    if (trimmed && !value.includes(trimmed)) {
      onChange([...value, trimmed]);
      setInput('');
      onEdit?.();
    }
  };

  const remove = (item: string) => {
    onChange(value.filter((v) => v !== item));
    onEdit?.();
  };

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-1.5">
        {value.map((item) => (
          <Badge key={item} variant="secondary" className="gap-1 pr-1">
            {item}
            <button
              type="button"
              onClick={() => remove(item)}
              className="hover:bg-muted rounded-full p-0.5"
              aria-label={`Remove ${item}`}
            >
              <X className="w-3 h-3" />
            </button>
          </Badge>
        ))}
      </div>
      <div className="flex gap-2">
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              e.preventDefault();
              add();
            }
          }}
          placeholder={placeholder}
          className="flex-1"
        />
        <Button type="button" variant="outline" size="sm" onClick={add} disabled={!input.trim()}>
          Add
        </Button>
      </div>
      {autoDetected && (
        <span className="inline-flex items-center gap-1 text-xs text-primary">
          <Sparkles className="w-3 h-3" />
          Auto-detected
        </span>
      )}
    </div>
  );
}

// Auto-detected chip for individual fields
function AutoDetectedChip({ visible }: { visible: boolean }) {
  if (!visible) return null;
  return (
    <span className="inline-flex items-center gap-1 text-xs text-primary ml-2">
      <Sparkles className="w-3 h-3" />
      Auto-detected
    </span>
  );
}

const LANGUAGES = [
  { value: 'en', label: 'English' },
  { value: 'es', label: 'Spanish' },
  { value: 'fr', label: 'French' },
  { value: 'de', label: 'German' },
  { value: 'zh', label: 'Chinese' },
  { value: 'ja', label: 'Japanese' },
  { value: 'ko', label: 'Korean' },
  { value: 'pt', label: 'Portuguese' },
  { value: 'ar', label: 'Arabic' },
  { value: 'hi', label: 'Hindi' },
];

export function MetadataForm({ sourceType, initialData, onSubmit, disabled }: MetadataFormProps) {
  const navigate = useNavigate();
  const typeConfig = SOURCE_TYPE_CONFIG[sourceType];

  const [title, setTitle] = useState(initialData?.title ?? '');
  const [authors, setAuthors] = useState<string[]>(initialData?.authors ?? []);
  const [publicationDate, setPublicationDate] = useState(initialData?.publicationDate ?? '');
  const [publisher, setPublisher] = useState(initialData?.publisher ?? '');
  const [url, setUrl] = useState((initialData?.url as string) ?? '');
  const [doi, setDoi] = useState(initialData?.doi ?? '');
  const [language, setLanguage] = useState(initialData?.language ?? '');
  const [description, setDescription] = useState(initialData?.description ?? '');
  const [tags, setTags] = useState<string[]>(initialData?.tags ?? []);
  const [contentSensitivity, setContentSensitivity] = useState<ContentSensitivity | ''>(
    (initialData?.contentSensitivity as ContentSensitivity) ?? ''
  );
  const [internalNotes, setInternalNotes] = useState(initialData?.internalNotes ?? '');

  // Track which auto-detected fields have been edited
  const [editedFields, setEditedFields] = useState<Set<string>>(new Set());

  const markEdited = useCallback((field: string) => {
    setEditedFields((prev) => new Set(prev).add(field));
  }, []);

  const isAutoDetected = (field: string) =>
    initialData && field in initialData && !editedFields.has(field);

  // Validation
  const errors = useMemo(() => {
    const result = sourceMetadataSchema.safeParse({
      title,
      authors,
      publicationDate: publicationDate || null,
      publisher: publisher || null,
      url: url,
      doi: doi || null,
      language: language || null,
      description: description || null,
      tags,
      contentSensitivity: contentSensitivity || undefined,
      internalNotes: internalNotes || null,
    });

    if (result.success) return {};
    const fieldErrors: Record<string, string> = {};
    for (const issue of result.error.issues) {
      const key = String(issue.path[0]);
      if (!fieldErrors[key]) {
        fieldErrors[key] = issue.message;
      }
    }
    return fieldErrors;
  }, [title, authors, publicationDate, publisher, url, doi, language, description, tags, contentSensitivity, internalNotes]);

  const missingRequired: string[] = [];
  if (!title.trim()) missingRequired.push('Title');
  if (authors.length === 0) missingRequired.push('Authors');
  if (!url.trim()) missingRequired.push('URL');
  if (!contentSensitivity) missingRequired.push('Content Sensitivity');

  const handleSubmit = () => {
    const data: SourceMetadataFormData = {
      title,
      authors,
      publicationDate: publicationDate || null,
      publisher: publisher || null,
      url: url,
      doi: doi || null,
      language: language || null,
      description: description || null,
      tags,
      contentSensitivity: contentSensitivity as ContentSensitivity,
      internalNotes: internalNotes || null,
    };

    const result = sourceMetadataSchema.safeParse(data);
    if (!result.success) {
      toast.error('Please fill in all required fields');
      return;
    }

    onSubmit(result.data);
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold font-display">Source metadata</h2>
        <p className="text-sm text-muted-foreground mt-1">
          Fill in the metadata for your {typeConfig.label.toLowerCase()}. Auto-detected fields are
          pre-populated.
        </p>
      </div>

      <div className="space-y-5 max-w-2xl">
        {/* Title */}
        <div className="space-y-2">
          <Label htmlFor="title" className="flex items-center">
            Title <span className="text-destructive ml-1">*</span>
            <AutoDetectedChip visible={!!isAutoDetected('title')} />
          </Label>
          <Input
            id="title"
            value={title}
            onChange={(e) => {
              setTitle(e.target.value);
              markEdited('title');
            }}
            placeholder="Enter source title"
            aria-invalid={!!errors.title}
          />
          {errors.title && <p className="text-xs text-destructive">{errors.title}</p>}
        </div>

        {/* Authors */}
        <div className="space-y-2">
          <Label className="flex items-center">
            Authors <span className="text-destructive ml-1">*</span>
            <AutoDetectedChip visible={!!isAutoDetected('authors')} />
          </Label>
          <ChipInput
            value={authors}
            onChange={(v) => {
              setAuthors(v);
              markEdited('authors');
            }}
            placeholder="Add author and press Enter"
            autoDetected={!!isAutoDetected('authors')}
            onEdit={() => markEdited('authors')}
          />
          {errors.authors && <p className="text-xs text-destructive">{errors.authors}</p>}
        </div>

        {/* Publication date */}
        <div className="space-y-2">
          <Label htmlFor="pub-date" className="flex items-center">
            Publication date <span className="text-destructive ml-1">*</span>
            <AutoDetectedChip visible={!!isAutoDetected('publicationDate')} />
          </Label>
          <Input
            id="pub-date"
            type="date"
            value={publicationDate}
            onChange={(e) => {
              setPublicationDate(e.target.value);
              markEdited('publicationDate');
            }}
            aria-invalid={!!errors.publicationDate}
          />
          {errors.publicationDate && (
            <p className="text-xs text-destructive">{errors.publicationDate}</p>
          )}
        </div>

        {/* Source type (auto) */}
        <div className="space-y-2">
          <Label>Source type</Label>
          <Input value={typeConfig.label} disabled className="bg-muted" />
        </div>

        <Separator />

        {/* Publisher */}
        <div className="space-y-2">
          <Label htmlFor="publisher" className="flex items-center">
            Publisher / Outlet
            <AutoDetectedChip visible={!!isAutoDetected('publisher')} />
          </Label>
          <Input
            id="publisher"
            value={publisher}
            onChange={(e) => {
              setPublisher(e.target.value);
              markEdited('publisher');
            }}
            placeholder="e.g., Nature, arXiv, Internal Report"
          />
        </div>

        {/* URL/DOI */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="source-url">URL</Label>
            <Input
              id="source-url"
              value={url}
              onChange={(e) => {
                setUrl(e.target.value);
                markEdited('url');
              }}
              placeholder="https://..."
              aria-invalid={!!errors.url}
            />
            {errors.url && <p className="text-xs text-destructive">{errors.url}</p>}
          </div>
          <div className="space-y-2">
            <Label htmlFor="doi">DOI</Label>
            <Input
              id="doi"
              value={doi}
              onChange={(e) => {
                setDoi(e.target.value);
                markEdited('doi');
              }}
              placeholder="10.1234/..."
            />
          </div>
        </div>

        {/* Language */}
        <div className="space-y-2">
          <Label htmlFor="language">Language</Label>
          <Select value={language} onValueChange={(v) => setLanguage(v)}>
            <SelectTrigger id="language">
              <SelectValue placeholder="Select language" />
            </SelectTrigger>
            <SelectContent>
              {LANGUAGES.map((l) => (
                <SelectItem key={l.value} value={l.value}>
                  {l.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Description */}
        <div className="space-y-2">
          <Label htmlFor="description" className="flex items-center">
            Description / Abstract
            <AutoDetectedChip visible={!!isAutoDetected('description')} />
          </Label>
          <Textarea
            id="description"
            value={description ?? ''}
            onChange={(e) => {
              setDescription(e.target.value);
              markEdited('description');
            }}
            placeholder="Brief description or abstract of the source content"
            rows={3}
          />
        </div>

        {/* Tags */}
        <div className="space-y-2">
          <Label>Tags / Topics</Label>
          <ChipInput
            value={tags}
            onChange={setTags}
            placeholder="Add a tag and press Enter"
          />
        </div>

        {/* Content Sensitivity */}
        <div className="space-y-2">
          <Label className="flex items-center gap-1">
            Content sensitivity level <span className="text-destructive ml-1">*</span>
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <button type="button" className="text-muted-foreground hover:text-foreground" aria-label="Sensitivity level info">
                    <Info className="w-4 h-4" />
                  </button>
                </TooltipTrigger>
                <TooltipContent side="right" className="w-72 p-3">
                  <div className="space-y-2 text-xs">
                    {SENSITIVITY_OPTIONS.map((opt) => (
                      <div key={opt.value}>
                        <strong>{opt.label}:</strong> {opt.description}
                      </div>
                    ))}
                  </div>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </Label>
          <Select
            value={contentSensitivity}
            onValueChange={(v) => setContentSensitivity(v as ContentSensitivity)}
          >
            <SelectTrigger aria-invalid={!!errors.contentSensitivity}>
              <SelectValue placeholder="Select sensitivity level" />
            </SelectTrigger>
            <SelectContent>
              {SENSITIVITY_OPTIONS.map((opt) => (
                <SelectItem key={opt.value} value={opt.value}>
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {errors.contentSensitivity && (
            <p className="text-xs text-destructive">{errors.contentSensitivity}</p>
          )}
        </div>

        {/* Internal Notes */}
        <div className="space-y-2">
          <Label htmlFor="notes">Internal notes</Label>
          <Textarea
            id="notes"
            value={internalNotes ?? ''}
            onChange={(e) => setInternalNotes(e.target.value)}
            placeholder="Internal notes (not visible to end users)"
            rows={2}
          />
        </div>
      </div>

      {/* Sticky footer with missing fields summary */}
      {missingRequired.length > 0 && (
        <div className="sticky bottom-0 left-0 right-0 bg-background/95 backdrop-blur border-t p-4 -mx-6 -mb-6 mt-6 z-10">
          <div className="flex items-center justify-between max-w-2xl">
            <p className="text-sm text-destructive">
              Missing required: {missingRequired.join(', ')}
            </p>
            <Button disabled={disabled}>
              {disabled ? 'Saving…' : 'Save source'}
            </Button>
          </div>
        </div>
      )}

      {missingRequired.length === 0 && (
        <div className="flex justify-end max-w-2xl">
          <Button onClick={handleSubmit} disabled={disabled}>
            {disabled ? 'Saving…' : 'Save source'}
          </Button>
        </div>
      )}
    </div>
  );
}
