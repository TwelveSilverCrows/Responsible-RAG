'use client';

import { useState, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import rehypeHighlight from 'rehype-highlight';
import { motion, AnimatePresence } from 'framer-motion';
import { Copy, Check, ThumbsUp, ThumbsDown } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import type { Message } from '@/types/chat';
import { CitationList } from '@/components/chat/CitationCard';

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const isStreaming = message.isStreaming;

  if (isUser) {
    return <UserBubble content={message.content} />;
  }

  return (
    <AssistantBubble
      content={message.content}
      citations={message.citations}
      isStreaming={isStreaming ?? false}
    />
  );
}

function UserBubble({ content }: { content: string }) {
  return (
    <div className="flex justify-end">
      <div className="max-w-[80%] sm:max-w-[70%] bg-primary text-primary-foreground px-4 py-2.5 rounded-2xl rounded-br-md text-sm leading-relaxed">
        {content}
      </div>
    </div>
  );
}

function AssistantBubble({
  content,
  citations,
  isStreaming,
}: {
  content: string;
  citations: Message['citations'];
  isStreaming: boolean;
}) {
  const [copied, setCopied] = useState(false);
  const [reaction, setReaction] = useState<'up' | 'down' | null>(null);

  const handleCopy = useCallback(() => {
    navigator.clipboard.writeText(content).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }, [content]);

  return (
    <div className="flex justify-start">
      <div
        className="max-w-[85%] sm:max-w-[75%] bg-card border rounded-2xl rounded-bl-md px-4 py-3 text-sm leading-relaxed shadow-sm"
        aria-live={isStreaming ? 'polite' : undefined}
      >
        {/* Markdown content */}
        <div className="prose prose-sm max-w-none dark:prose-invert prose-p:my-1 prose-headings:my-2 prose-ul:my-1 prose-ol:my-1 prose-li:my-0.5 prose-pre:my-2 prose-pre:bg-muted/50 prose-pre:border prose-pre:border-border/50 prose-code:text-primary">
          <ReactMarkdown rehypePlugins={[rehypeHighlight]}>{content}</ReactMarkdown>
          {isStreaming && <StreamingCursor />}
        </div>

        {/* Action buttons — shown when not streaming */}
        {!isStreaming && (
          <div className="flex items-center justify-between mt-2 pt-2 border-t border-border/30">
            <button
              onClick={handleCopy}
              className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
              aria-label="Copy message"
            >
              {copied ? (
                <>
                  <Check className="w-3.5 h-3.5" />
                  Copied
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5" />
                  Copy
                </>
              )}
            </button>

            <div className="flex items-center gap-1">
              <Button
                variant="ghost"
                size="icon"
                className={cn(
                  'h-7 w-7',
                  reaction === 'up'
                    ? 'text-primary bg-primary/10'
                    : 'text-muted-foreground'
                )}
                onClick={() => setReaction(reaction === 'up' ? null : 'up')}
                aria-label="Thumbs up"
              >
                <ThumbsUp className="w-3.5 h-3.5" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className={cn(
                  'h-7 w-7',
                  reaction === 'down'
                    ? 'text-destructive bg-destructive/10'
                    : 'text-muted-foreground'
                )}
                onClick={() => setReaction(reaction === 'down' ? null : 'down')}
                aria-label="Thumbs down"
              >
                <ThumbsDown className="w-3.5 h-3.5" />
              </Button>
            </div>
          </div>
        )}

        {/* Citation cards — shown after streaming completes */}
        <AnimatePresence>
          {!isStreaming && citations.length > 0 && (
            <CitationList citations={citations} />
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

function StreamingCursor() {
  return (
    <span className="inline-block w-0.5 h-4 bg-foreground/70 ml-0.5 align-text-bottom animate-blink" />
  );
}
