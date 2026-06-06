import { z } from 'zod/v4';

export const sourceMetadataSchema = z.object({
  title: z.string().min(1, 'Title is required'),
  authors: z.array(z.string()).min(1, 'At least one author is required'),
  publicationDate: z.string().nullable().optional(),
  publisher: z.string().nullable().optional(),
  url: z.string().url('Please enter a valid URL').nullable().optional().or(z.literal('')),
  doi: z.string().nullable().optional(),
  language: z.string().nullable().optional(),
  description: z.string().nullable().optional(),
  tags: z.array(z.string()).optional(),
  contentSensitivity: z.enum(['low', 'medium', 'high'], {
    message: 'Content sensitivity level is required',
  }),
  internalNotes: z.string().nullable().optional(),
});

export type SourceMetadataFormData = z.infer<typeof sourceMetadataSchema>;

export const urlInputSchema = z.object({
  url: z.url('Please enter a valid URL'),
});

export type UrlInputFormData = z.infer<typeof urlInputSchema>;
