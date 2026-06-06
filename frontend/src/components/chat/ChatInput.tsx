'use client';

import { useState, useRef, useCallback, useEffect, type KeyboardEvent } from 'react';
import { ArrowUp, Paperclip, Mic } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Tooltip, TooltipTrigger, TooltipContent } from '@/components/ui/tooltip';
import { cn } from '@/lib/utils';
import { useConsentStore } from '@/stores/consentStore';
import { getChatPrivacyNotice } from '@/lib/utils/privacyHelpers';
import Link from 'next/link';

interface ChatInputProps {
  onSend: (content: string) => void;
  disabled?: boolean;
}

const MAX_CHARS = 4000;
const SHOW_COUNT_THRESHOLD = 500;

export function ChatInput({ onSend, disabled = false }: ChatInputProps) {
  const [value, setValue] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { profileMode } = useConsentStore();
  const privacy = getChatPrivacyNotice(profileMode);

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    const lineHeight = parseFloat(getComputedStyle(el).lineHeight) || 24;
    const maxHeight = lineHeight * 5;
    el.style.height = `${Math.min(el.scrollHeight, maxHeight)}px`;
  }, [value]);

  const canSend = value.trim().length > 0 && !disabled && value.length <= MAX_CHARS;

  const handleSend = useCallback(() => {
    if (!canSend) return;
    onSend(value.trim());
    setValue('');
    // Return focus to input after send
    requestAnimationFrame(() => {
      textareaRef.current?.focus();
    });
  }, [canSend, onSend, value]);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    },
    [handleSend]
  );

  return (
    <div className="border-t bg-card px-4 py-3">
      <div className="max-w-3xl mx-auto">
        {/* Input area */}
        <div className="relative flex items-end gap-2 rounded-xl border bg-background px-3 py-2 focus-within:ring-2 focus-within:ring-ring focus-within:ring-offset-1 transition-shadow">
          {/* File attachment (disabled) */}
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 flex-shrink-0 text-muted-foreground opacity-50 cursor-not-allowed"
                disabled
                aria-label="Attach file (coming soon)"
              >
                <Paperclip className="w-4 h-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>Coming soon</TooltipContent>
          </Tooltip>

          {/* Textarea */}
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => {
              if (e.target.value.length <= MAX_CHARS) setValue(e.target.value);
            }}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question..."
            disabled={disabled}
            rows={1}
            className={cn(
              'flex-1 resize-none bg-transparent text-sm leading-6 placeholder:text-muted-foreground focus:outline-none',
              'max-h-[120px] overflow-y-auto custom-scrollbar'
            )}
            aria-label="Chat message input"
          />

          {/* Voice input (disabled) */}
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 flex-shrink-0 text-muted-foreground opacity-50 cursor-not-allowed"
                disabled
                aria-label="Voice input (coming soon)"
              >
                <Mic className="w-4 h-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>Coming soon</TooltipContent>
          </Tooltip>

          {/* Send button */}
          <Button
            size="icon"
            className={cn(
              'h-8 w-8 flex-shrink-0 rounded-lg transition-all',
              canSend
                ? 'bg-primary hover:bg-primary/90 text-primary-foreground'
                : 'bg-muted text-muted-foreground cursor-not-allowed'
            )}
            onClick={handleSend}
            disabled={!canSend}
            aria-label="Send message"
          >
            <ArrowUp className="w-4 h-4" />
          </Button>
        </div>

        {/* Character count + privacy notice */}
        <div className="flex items-center justify-between mt-1.5 px-1">
          <div className="text-xs text-muted-foreground">
            {profileMode === 'general' ? (
              <span className="inline-flex items-center gap-1">
                🔒 General mode — no personal data is stored or used.
              </span>
            ) : (
              <span>
                Responses are personalized to your profile.{' '}
                <Link
                  href="/profile"
                  className="text-primary hover:underline"
                >
                  Edit profile
                </Link>
              </span>
            )}
          </div>
          {value.length > SHOW_COUNT_THRESHOLD && (
            <span
              className={cn(
                'text-xs tabular-nums',
                value.length > MAX_CHARS * 0.9
                  ? 'text-destructive'
                  : 'text-muted-foreground'
              )}
            >
              {value.length}/{MAX_CHARS}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
