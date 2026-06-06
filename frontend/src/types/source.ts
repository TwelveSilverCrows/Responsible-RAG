export type SourceType = 'pdf' | 'text' | 'audio' | 'webpage' | 'youtube';

export type SourceStatus = 'queued' | 'processing' | 'indexed' | 'error';

export type ContentSensitivity = 'low' | 'medium' | 'high';

export interface Source {
  id: string;
  title: string;
  type: SourceType;
  authors: string[];
  publicationDate: string | null;
  publisher: string | null;
  url: string | null;
  doi: string | null;
  language: string | null;
  description: string | null;
  tags: string[];
  contentSensitivity: ContentSensitivity;
  internalNotes: string | null;
  status: SourceStatus;
  errorMessage: string | null;
  indexedAt: string | null;
  createdAt: string;
  updatedAt: string;
  filePath: string | null;
  thumbnailUrl: string | null;
}

export const SOURCE_TYPE_CONFIG: Record<SourceType, { label: string; icon: string; acceptTypes: string; color: string }> = {
  pdf: {
    label: 'PDF Document',
    icon: 'FileText',
    acceptTypes: '.pdf',
    color: 'text-red-500',
  },
  text: {
    label: 'Text / Markdown File',
    icon: 'FileCode',
    acceptTypes: '.txt,.md,.markdown,.rst',
    color: 'text-blue-500',
  },
  audio: {
    label: 'Audio File',
    icon: 'Mic',
    acceptTypes: '.mp3,.wav,.m4a,.ogg,.flac',
    color: 'text-purple-500',
  },
  webpage: {
    label: 'Webpage URL',
    icon: 'Globe',
    acceptTypes: '',
    color: 'text-green-500',
  },
  youtube: {
    label: 'YouTube Video',
    icon: 'Youtube',
    acceptTypes: '',
    color: 'text-rose-500',
  },
};

export const SENSITIVITY_OPTIONS: { value: ContentSensitivity; label: string; description: string }[] = [
  { value: 'low', label: 'Low', description: 'Publicly available information with no personal or sensitive content.' },
  { value: 'medium', label: 'Medium', description: 'Contains some sensitive information that may need additional access controls.' },
  { value: 'high', label: 'High', description: 'Contains highly sensitive information requiring strict access controls and special handling.' },
];
