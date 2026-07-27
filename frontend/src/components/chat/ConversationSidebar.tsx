'use client';

import { useState, useMemo, useCallback } from 'react';
import { formatDistanceToNow } from 'date-fns';
import {
  Plus,
  Search,
  MessageSquare,
  Trash2,
  Pencil,
  Check,
  X,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import {
  ContextMenu,
  ContextMenuContent,
  ContextMenuItem,
  ContextMenuTrigger,
} from '@/components/ui/context-menu';
import { useChatStore } from '@/stores/chatStore';
import { cn } from '@/lib/utils';
import { toast } from 'sonner';
import type { Conversation } from '@/types/chat';

interface ConversationSidebarProps {
  onNewConversation: () => void;
  onSelectConversation: (id: string) => void;
  isMobile?: boolean;
}

function groupConversations(conversations: Conversation[]) {
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);

  const groups: { label: string; conversations: Conversation[] }[] = [
    { label: 'Today', conversations: [] },
    { label: 'Yesterday', conversations: [] },
    { label: 'Older', conversations: [] },
  ];

  for (const conv of conversations) {
    const date = new Date(conv.lastMessageAt);
    if (date >= today) {
      groups[0].conversations.push(conv);
    } else if (date >= yesterday) {
      groups[1].conversations.push(conv);
    } else {
      groups[2].conversations.push(conv);
    }
  }

  return groups.filter((g) => g.conversations.length > 0);
}

function ConversationItem({
  conversation,
  isActive,
  onSelect,
  onDelete,
  onRename,
}: {
  conversation: Conversation;
  isActive: boolean;
  onSelect: () => void;
  onDelete: () => void;
  onRename: (title: string) => void;
}) {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(conversation.title);

  const handleSaveRename = useCallback(() => {
    const trimmed = editValue.trim();
    if (trimmed && trimmed !== conversation.title) {
      onRename(trimmed);
    }
    setIsEditing(false);
  }, [editValue, conversation.title, onRename]);

  const handleCancelRename = useCallback(() => {
    setEditValue(conversation.title);
    setIsEditing(false);
  }, [conversation.title]);

  const handleDoubleClick = useCallback(() => {
    setEditValue(conversation.title);
    setIsEditing(true);
  }, [conversation.title]);

  const relativeTime = formatDistanceToNow(new Date(conversation.lastMessageAt), {
    addSuffix: false,
  });

  return (
    <ContextMenu>
      <ContextMenuTrigger asChild>
        <button
          onClick={onSelect}
          onDoubleClick={handleDoubleClick}
          className={cn(
            'w-full text-left px-3 py-2.5 rounded-lg transition-colors group',
            isActive
              ? 'bg-primary/10 text-primary'
              : 'hover:bg-accent text-foreground'
          )}
        >
          {isEditing ? (
            <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
              <Input
                value={editValue}
                onChange={(e) => setEditValue(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleSaveRename();
                  if (e.key === 'Escape') handleCancelRename();
                }}
                className="h-7 text-sm"
                autoFocus
              />
              <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6 flex-shrink-0"
                onClick={handleSaveRename}
                aria-label="Save rename"
              >
                <Check className="w-3 h-3" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6 flex-shrink-0"
                onClick={handleCancelRename}
                aria-label="Cancel rename"
              >
                <X className="w-3 h-3" />
              </Button>
            </div>
          ) : (
            <>
              <p
                className="text-sm font-medium leading-snug line-clamp-2"
                title={conversation.title}
              >
                {conversation.title}
              </p>
              <div className="flex items-center gap-2 mt-0.5">
                <p className="text-xs text-muted-foreground truncate flex-1">
                  {conversation.lastMessage ?? 'No messages'}
                </p>
                <span className="text-xs text-muted-foreground flex-shrink-0">
                  {relativeTime}
                </span>
              </div>
            </>
          )}
        </button>
      </ContextMenuTrigger>
      <ContextMenuContent>
        <ContextMenuItem
          onClick={() => {
            setEditValue(conversation.title);
            setIsEditing(true);
          }}
        >
          <Pencil className="w-4 h-4 mr-2" />
          Rename
        </ContextMenuItem>
        <ContextMenuItem onClick={onDelete} className="text-destructive focus:text-destructive">
          <Trash2 className="w-4 h-4 mr-2" />
          Delete
        </ContextMenuItem>
      </ContextMenuContent>
    </ContextMenu>
  );
}

export function ConversationSidebar({
  onNewConversation,
  onSelectConversation,
  isMobile = false,
}: ConversationSidebarProps) {
  const {
    conversations,
    activeConversationId,
    removeConversation,
    renameConversation,
  } = useChatStore();

  const [searchQuery, setSearchQuery] = useState('');
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null);

  const filteredConversations = useMemo(() => {
    if (!searchQuery.trim()) return conversations;
    const q = searchQuery.toLowerCase();
    return conversations.filter(
      (c) =>
        c.title.toLowerCase().includes(q) ||
        (c.lastMessage && c.lastMessage.toLowerCase().includes(q))
    );
  }, [conversations, searchQuery]);

  const grouped = useMemo(
    () => groupConversations(filteredConversations),
    [filteredConversations]
  );

  const handleDelete = useCallback(
    (id: string) => {
      const conv = conversations.find((c) => c.id === id);
      removeConversation(id);
      setDeleteTarget(null);
      if (conv) {
        toast(`Deleted "${conv.title}"`, {
          action: {
            label: 'Undo',
            onClick: () => {
              // Re-add the conversation optimistically
              useChatStore.getState().addConversation(conv);
            },
          },
          duration: 5000,
        });
      }
    },
    [conversations, removeConversation]
  );

  return (
    <div className="flex flex-col h-full bg-sidebar">
      {/* Header */}
      <div className="p-3 border-b border-sidebar-border space-y-2">
        <Button
          onClick={onNewConversation}
          className="w-full justify-start gap-2"
          size="sm"
        >
          <Plus className="w-4 h-4" />
          New conversation
        </Button>
        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
          <Input
            placeholder="Search conversations…"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-8 h-8 text-sm"
          />
        </div>
      </div>

      {/* Conversation list */}
      <ScrollArea className="flex-1">
        <div className="p-2 space-y-4">
          {grouped.length === 0 && (
            <div className="text-center py-8 px-4">
              <MessageSquare className="w-8 h-8 text-muted-foreground mx-auto mb-2" />
              <p className="text-sm text-muted-foreground">
                {searchQuery ? 'No matching conversations' : 'No conversations yet'}
              </p>
              {!searchQuery && (
                <Button
                  variant="link"
                  size="sm"
                  onClick={onNewConversation}
                  className="text-primary mt-1"
                >
                  Start your first conversation
                </Button>
              )}
            </div>
          )}

          {grouped.map((group) => (
            <div key={group.label}>
              <p className="px-3 py-1 text-xs font-medium text-muted-foreground uppercase tracking-wider">
                {group.label}
              </p>
              <div className="space-y-0.5">
                {group.conversations.map((conv) => (
                  <ConversationItem
                    key={conv.id}
                    conversation={conv}
                    isActive={conv.id === activeConversationId}
                    onSelect={() => onSelectConversation(conv.id)}
                    onDelete={() => setDeleteTarget(conv.id)}
                    onRename={(title) => renameConversation(conv.id, title)}
                  />
                ))}
              </div>
            </div>
          ))}
        </div>
      </ScrollArea>

      {/* Delete confirmation dialog */}
      <AlertDialog
        open={deleteTarget !== null}
        onOpenChange={(open) => {
          if (!open) setDeleteTarget(null);
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete conversation?</AlertDialogTitle>
            <AlertDialogDescription>
              This conversation will be permanently deleted. You can undo this action for 5 seconds.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                if (deleteTarget) handleDelete(deleteTarget);
              }}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
