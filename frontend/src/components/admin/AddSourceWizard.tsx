'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { SourceTypeSelector } from '@/components/admin/SourceTypeSelector';
import { FileUploadZone } from '@/components/admin/FileUploadZone';
import { UrlInputCard } from '@/components/admin/UrlInputCard';
import { MetadataForm } from '@/components/admin/MetadataForm';
import type { SourceType } from '@/types/source';
import type { SourceMetadataFormData } from '@/lib/schemas/source.schema';
import type { ExtractedMetadata } from '@/lib/utils/metadataExtractor';
import { cn } from '@/lib/utils';

type WizardStep = 'type' | 'upload' | 'metadata';

interface StepConfig {
  key: WizardStep;
  label: string;
  number: number;
}

const steps: StepConfig[] = [
  { key: 'type', label: 'Source Type', number: 1 },
  { key: 'upload', label: 'Upload Content', number: 2 },
  { key: 'metadata', label: 'Metadata', number: 3 },
];

const fileTypes: SourceType[] = ['pdf', 'text', 'audio'];
const urlTypes: SourceType[] = ['webpage', 'youtube'];

interface UploadedFileData {
  id: string;
  file: File;
  progress: number;
  status: 'uploading' | 'complete' | 'error';
}

export function AddSourceWizard() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState<WizardStep>('type');
  const [selectedType, setSelectedType] = useState<SourceType | null>(null);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFileData[]>([]);
  const [urlValue, setUrlValue] = useState('');
  const [fetchedMetadata, setFetchedMetadata] = useState<ExtractedMetadata | null>(null);

  const stepIndex = steps.findIndex((s) => s.key === currentStep);

  const goToStep = (step: WizardStep) => setCurrentStep(step);

  const handleTypeSelect = (type: SourceType) => {
    setSelectedType(type);
    goToStep('upload');
  };

  const handleUploadComplete = (files: UploadedFileData[]) => {
    setUploadedFiles(files);
    goToStep('metadata');
  };

  const handleMetadataFetched = (url: string, metadata: ExtractedMetadata) => {
    setUrlValue(url);
    setFetchedMetadata(metadata);
    // Don't auto-advance — let user review the preview first
  };

  const handleUrlContinue = () => {
    goToStep('metadata');
  };

  const handleMetadataSubmit = (data: SourceMetadataFormData) => {
    // In a real app, this would call an API to create the source
    void data;
    router.push('/admin/sources');
  };

  const handleBack = () => {
    if (currentStep === 'upload') {
      setCurrentStep('type');
    } else if (currentStep === 'metadata') {
      setCurrentStep('upload');
    }
  };

  // Build initial data for metadata form from fetched metadata
  const metadataInitialData: Partial<SourceMetadataFormData> | undefined = fetchedMetadata
    ? {
        title: fetchedMetadata.title ?? undefined,
        authors: fetchedMetadata.authors,
        publicationDate: fetchedMetadata.publicationDate ?? undefined,
        publisher: fetchedMetadata.publisher ?? undefined,
        description: fetchedMetadata.description ?? undefined,
        language: fetchedMetadata.language ?? undefined,
      }
    : undefined;

  return (
    <div className="space-y-8">
      {/* Step indicator */}
      <div className="flex items-center justify-center gap-2">
        {steps.map((step, i) => {
          const isActive = step.key === currentStep;
          const isComplete = i < stepIndex;
          return (
            <div key={step.key} className="flex items-center">
              {i > 0 && (
                <div
                  className={cn(
                    'w-8 sm:w-16 h-0.5 mx-1',
                    isComplete ? 'bg-primary' : 'bg-muted-foreground/20'
                  )}
                />
              )}
              <div className="flex items-center gap-2">
                <div
                  className={cn(
                    'w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold border-2 transition-colors',
                    isActive
                      ? 'border-primary bg-primary text-primary-foreground'
                      : isComplete
                        ? 'border-primary bg-primary text-primary-foreground'
                        : 'border-muted-foreground/30 text-muted-foreground bg-background'
                  )}
                >
                  {isComplete ? <Check className="w-4 h-4" /> : step.number}
                </div>
                <span
                  className={cn(
                    'text-sm font-medium hidden sm:inline',
                    isActive ? 'text-foreground' : 'text-muted-foreground'
                  )}
                >
                  {step.label}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Step content */}
      <div>
        {currentStep === 'type' && (
          <SourceTypeSelector value={selectedType} onChange={handleTypeSelect} />
        )}

        {currentStep === 'upload' && selectedType && (
          <div className="space-y-6">
            {fileTypes.includes(selectedType) && (
              <FileUploadZone
                sourceType={selectedType}
                onUploadComplete={handleUploadComplete}
              />
            )}
            {urlTypes.includes(selectedType) && (
              <div className="space-y-4">
                <UrlInputCard
                  sourceType={selectedType}
                  onMetadataFetched={handleMetadataFetched}
                />
                {fetchedMetadata && (
                  <div className="flex justify-end">
                    <Button onClick={handleUrlContinue}>
                      Continue to metadata →
                    </Button>
                  </div>
                )}
              </div>
            )}
            <div className="flex justify-start">
              <Button variant="outline" onClick={handleBack}>
                ← Back
              </Button>
            </div>
          </div>
        )}

        {currentStep === 'metadata' && selectedType && (
          <div className="space-y-6">
            <MetadataForm
              sourceType={selectedType}
              initialData={metadataInitialData}
              onSubmit={handleMetadataSubmit}
            />
            <div className="flex justify-start">
              <Button variant="outline" onClick={handleBack}>
                ← Back
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
