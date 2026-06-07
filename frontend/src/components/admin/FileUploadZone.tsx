'use client';

import { useState, useCallback } from 'react';
import { Upload, X, FileText, FileCode, Mic, AlertCircle } from 'lucide-react';
import { useDropzone } from 'react-dropzone';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import type { SourceType } from '@/types/source';
import { SOURCE_TYPE_CONFIG } from '@/types/source';

const typeIcons: Record<string, React.ElementType> = {
  pdf: FileText,
  text: FileCode,
  audio: Mic,
};

interface UploadedFile {
  id: string;
  file: File;
  progress: number;
  status: 'uploading' | 'complete' | 'error';
  error?: string;
}

interface FileUploadZoneProps {
  sourceType: SourceType;
  onUploadComplete: (files: UploadedFile[]) => void;
}

const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB

export function FileUploadZone({ sourceType, onUploadComplete }: FileUploadZoneProps) {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [error, setError] = useState<string | null>(null);
  const config = SOURCE_TYPE_CONFIG[sourceType];

  const acceptTypes = config.acceptTypes
    ? Object.fromEntries(
        config.acceptTypes.split(',').map((ext) => [ext.trim(), []])
      )
    : {};

  const simulateUpload = useCallback(
    (fileId: string) => {
      let progress = 0;
      const interval = setInterval(() => {
        progress += Math.random() * 20 + 5;
        if (progress >= 100) {
          progress = 100;
          clearInterval(interval);
          setFiles((prev) =>
            prev.map((f) =>
              f.id === fileId ? { ...f, progress: 100, status: 'complete' } : f
            )
          );
        } else {
          setFiles((prev) =>
            prev.map((f) =>
              f.id === fileId ? { ...f, progress: Math.min(progress, 99) } : f
            )
          );
        }
      }, 400);
    },
    []
  );

  const onDrop = useCallback(
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (acceptedFiles: File[], rejectedFiles: any[]) => {
      setError(null);

      if (rejectedFiles.length > 0) {
        const firstError = rejectedFiles[0]?.errors[0]?.message;
        setError(firstError || 'Some files were rejected.');
        return;
      }

      const newFiles: UploadedFile[] = acceptedFiles.map((file) => ({
        id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
        file,
        progress: 0,
        status: 'uploading' as const,
      }));

      setFiles((prev) => [...prev, ...newFiles]);
      newFiles.forEach((f) => simulateUpload(f.id));
    },
    [simulateUpload]
  );

  const { getRootProps, getInputProps, isDragActive, open } = useDropzone({
    onDrop,
    accept: Object.keys(acceptTypes).length > 0 ? acceptTypes : undefined,
    maxSize: MAX_FILE_SIZE,
    multiple: true,
    noClick: false,
  });

  const cancelUpload = (fileId: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== fileId));
  };

  const allComplete = files.length > 0 && files.every((f) => f.status === 'complete');

  const handleContinue = () => {
    onUploadComplete(files);
  };

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-xl font-semibold font-display">Upload your files</h2>
        <p className="text-sm text-muted-foreground mt-1">
          Drag and drop {config.label.toLowerCase()} files, or browse to select.
        </p>
      </div>

      {/* Drop zone */}
      <div
        {...getRootProps()}
        className={`
          relative border-2 border-dashed rounded-xl p-8 text-center transition-colors cursor-pointer
          ${isDragActive ? 'border-primary bg-primary/5' : 'border-muted-foreground/25 hover:border-primary/50 hover:bg-muted/30'}
        `}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center gap-3">
          <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center">
            <Upload className="w-8 h-8 text-muted-foreground" />
          </div>
          {isDragActive ? (
            <p className="text-lg font-medium text-primary">Drop files here...</p>
          ) : (
            <>
              <p className="text-lg font-medium">
                Drag & drop files here
              </p>
              <p className="text-sm text-muted-foreground">or</p>
              <Button type="button" variant="outline" size="sm" onClick={(e) => { e.stopPropagation(); open(); }}>
                Browse files
              </Button>
            </>
          )}
          <p className="text-xs text-muted-foreground mt-2">
            Accepted: {config.acceptTypes || 'Any file'} • Maximum file size: 50MB
          </p>
        </div>
      </div>

      {/* Error */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="flex items-center gap-2 p-3 bg-destructive/10 text-destructive rounded-lg text-sm"
          >
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6 ml-auto"
              onClick={() => setError(null)}
            >
              <X className="w-3 h-3" />
            </Button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* File list */}
      {files.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-semibold">Uploaded files</h3>
          <div className="space-y-2">
            {files.map((f) => {
              const FileIcon = typeIcons[sourceType] || FileText;
              return (
                <div
                  key={f.id}
                  className="flex items-center gap-3 p-3 rounded-lg border bg-card"
                >
                  <FileIcon className="w-5 h-5 text-muted-foreground flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{f.file.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {(f.file.size / 1024 / 1024).toFixed(1)} MB
                    </p>
                    {f.status === 'uploading' && (
                      <Progress
                        value={f.progress}
                        className="h-1.5 mt-1.5"
                        aria-valuenow={Math.round(f.progress)}
                        aria-valuemin={0}
                        aria-valuemax={100}
                      />
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    {f.status === 'complete' && (
                      <span className="text-xs text-emerald-600 font-medium">Complete</span>
                    )}
                    {f.status === 'uploading' && (
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7"
                        onClick={() => cancelUpload(f.id)}
                        aria-label="Cancel upload"
                      >
                        <X className="w-4 h-4" />
                      </Button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Continue button */}
      {allComplete && (
        <div className="flex justify-end">
          <Button onClick={handleContinue}>
            Continue to metadata →
          </Button>
        </div>
      )}
    </div>
  );
}
