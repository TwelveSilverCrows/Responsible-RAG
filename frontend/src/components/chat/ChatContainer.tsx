'use client';

import { useEffect, useRef, useCallback, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  PanelLeftClose,
  PanelLeftOpen,
  PanelRightClose,
  PanelRightOpen,
  MessageSquarePlus,
  Shield,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Sheet, SheetContent } from '@/components/ui/sheet';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { useChatStore } from '@/stores/chatStore';
import { useConsentStore } from '@/stores/consentStore';
import { useProfileStore } from '@/stores/profileStore';
import { ProfileModeBadge } from '@/components/chat/ProfileModeBadge';
import { MessageBubble } from '@/components/chat/MessageBubble';
import { ChatInput } from '@/components/chat/ChatInput';
import { StreamingIndicator } from '@/components/chat/StreamingIndicator';
import { ConversationSidebar } from '@/components/chat/ConversationSidebar';
import { useIsMobile } from '@/hooks/use-mobile';
import {
  mockConversations,
  mockMessages,
  streamingResponses,
  mockCitations,
} from '@/lib/chatMockData';
import { cn } from '@/lib/utils';

// ── Context Panel ───────────────────────────────────────────
function ContextPanel() {
  const { profile } = useProfileStore();
  const { profileMode } = useConsentStore();

  return (
    <div className="p-4 space-y-4 text-sm">
      <h3 className="font-display font-semibold text-base">Profile Summary</h3>
      {profile ? (
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <span className="text-muted-foreground">Name:</span>
            <span>{profile.preferredName}</span>
          </div>
          {profile.primaryLanguage && (
            <div className="flex items-center gap-2">
              <span className="text-muted-foreground">Language:</span>
              <span>{profile.primaryLanguage}</span>
            </div>
          )}
          {profile.ageRange && (
            <div className="flex items-center gap-2">
              <span className="text-muted-foreground">Age range:</span>
              <span>{profile.ageRange.replace('_', '-')}</span>
            </div>
          )}
          <div className="flex items-center gap-2">
            <span className="text-muted-foreground">AI comfort:</span>
            <span>{profile.literacyComfortAI}/5</span>
          </div>
        </div>
      ) : (
        <p className="text-muted-foreground text-xs">No profile data available.</p>
      )}
      <Separator />
      <div className="space-y-2">
        <p className="text-muted-foreground text-xs">Active mode</p>
        <ProfileModeBadge variant="sidebar" />
      </div>
      <Separator />
      <div className="rounded-lg bg-muted/50 p-3 space-y-1">
        <div className="flex items-center gap-1.5 text-xs font-medium">
          <Shield className="w-3.5 h-3.5 text-primary" />
          Privacy notice
        </div>
        <p className="text-xs text-muted-foreground">
          {profileMode === 'full'
            ? 'Your profile is used to personalize responses. You can edit or delete it anytime.'
            : 'No personal data is stored. Responses are general.'}
        </p>
      </div>
    </div>
  );
}

// ── Welcome Screen ──────────────────────────────────────────
function WelcomeScreen({ onNewConversation }: { onNewConversation: () => void }) {
  return (
    <div className="flex-1 flex items-center justify-center p-8">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="text-center max-w-md space-y-4"
      >
        <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mx-auto">
          <MessageSquarePlus className="w-8 h-8 text-primary" />
        </div>
        <h2 className="font-display text-2xl font-semibold">
          Start a new conversation
        </h2>
        <p className="text-muted-foreground text-sm">
          Ask questions about responsible AI, RAG systems, privacy, or any topic.
          Responses are grounded in verified sources with full citations.
        </p>
        <Button onClick={onNewConversation} className="gap-2">
          <MessageSquarePlus className="w-4 h-4" />
          New conversation
        </Button>
      </motion.div>
    </div>
  );
}

// ── Main ChatContainer ──────────────────────────────────────
export function ChatContainer() {
  const navigate = useNavigate();
  const isMobile = useIsMobile();

  const {
    conversations,
    activeConversationId,
    messages,
    isStreaming,
    sidebarOpen,
    contextPanelOpen,
    setConversations,
    setMessages,
    setActiveConversationId,
    addMessage,
    updateMessage,
    addConversation,
    setStreaming,
    toggleSidebar,
    toggleContextPanel,
  } = useChatStore();

  const initializedRef = useRef(false);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const streamCountRef = useRef(0);

  // Initialize mock data on first mount
  useEffect(() => {
    if (!initializedRef.current && conversations.length === 0) {
      initializedRef.current = true;
      setConversations(mockConversations);
      setMessages(mockMessages);
    }
  }, [conversations.length, setConversations, setMessages]);

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isStreaming]);

  // Filter messages for active conversation
  const activeMessages = activeConversationId
    ? messages.filter((m) => m.conversationId === activeConversationId)
    : [];

  // ── Handlers ────────────────────────────────────────────
  const handleNewConversation = useCallback(() => {
    const id = `conv-${Date.now()}`;
    addConversation({
      id,
      title: 'New conversation',
      lastMessage: null,
      lastMessageAt: new Date().toISOString(),
      createdAt: new Date().toISOString(),
      messageCount: 0,
    });
    setActiveConversationId(id);
    navigate(`/chat/${id}`);
    if (isMobile) setMobileSidebarOpen(false);
  }, [addConversation, setActiveConversationId, navigate, isMobile]);

  const handleSelectConversation = useCallback(
    (id: string) => {
      setActiveConversationId(id);
      navigate(`/chat/${id}`);
      if (isMobile) setMobileSidebarOpen(false);
    },
    [setActiveConversationId, navigate, isMobile]
  );

  const handleSendMessage = useCallback(
    (content: string) => {
      if (!activeConversationId) return;

      // Add user message
      const userMsgId = `msg-${Date.now()}`;
      addMessage({
        id: userMsgId,
        conversationId: activeConversationId,
        role: 'user',
        content,
        citations: [],
        createdAt: new Date().toISOString(),
      });

      // Update conversation last message
      const conv = conversations.find((c) => c.id === activeConversationId);
      if (conv) {
        useChatStore.getState().renameConversation(
          activeConversationId,
          conv.title === 'New conversation'
            ? content.slice(0, 50) + (content.length > 50 ? '…' : '')
            : conv.title
        );
      }

      // Start streaming simulation
      const assistantMsgId = `msg-${Date.now() + 1}`;
      setStreaming(true);

      // Add streaming assistant message after a short delay
      setTimeout(() => {
        const responseIndex = streamCountRef.current % streamingResponses.length;
        streamCountRef.current += 1;
        const responseText = streamingResponses[responseIndex];

        addMessage({
          id: assistantMsgId,
          conversationId: activeConversationId,
          role: 'assistant',
          content: responseText,
          citations: [],
          createdAt: new Date().toISOString(),
          isStreaming: true,
        });

        // Complete streaming after another delay
        setTimeout(() => {
          updateMessage(assistantMsgId, {
            isStreaming: false,
            citations: [mockCitations[responseIndex % mockCitations.length]],
          });
          setStreaming(false);
        }, 1500);
      }, 800);
    },
    [activeConversationId, addMessage, setStreaming, updateMessage, conversations]
  );

  // ── Sidebar content (shared between desktop & mobile) ──
  const sidebarContent = (
    <ConversationSidebar
      onNewConversation={handleNewConversation}
      onSelectConversation={handleSelectConversation}
      isMobile={isMobile}
    />
  );

  return (
    <div className="flex h-full relative">
      {/* Desktop sidebar */}
      {!isMobile && sidebarOpen && (
        <motion.aside
          initial={{ width: 0, opacity: 0 }}
          animate={{ width: 280, opacity: 1 }}
          exit={{ width: 0, opacity: 0 }}
          transition={{ duration: 0.2 }}
          className="w-[280px] flex-shrink-0 border-r border-border overflow-hidden"
        >
          {sidebarContent}
        </motion.aside>
      )}

      {/* Mobile sidebar drawer */}
      {isMobile && (
        <Sheet open={mobileSidebarOpen} onOpenChange={setMobileSidebarOpen}>
          <SheetContent side="left" className="p-0 w-72">
            {sidebarContent}
          </SheetContent>
        </Sheet>
      )}

      {/* Main chat area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top bar */}
        <div className="flex items-center justify-between px-3 h-12 border-b bg-card flex-shrink-0">
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={() => {
                if (isMobile) setMobileSidebarOpen(true);
                else toggleSidebar();
              }}
              aria-label={sidebarOpen ? 'Close sidebar' : 'Open sidebar'}
            >
              {sidebarOpen && !isMobile ? (
                <PanelLeftClose className="w-4 h-4" />
              ) : (
                <PanelLeftOpen className="w-4 h-4" />
              )}
            </Button>
            <ProfileModeBadge variant="chat" />
          </div>
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={toggleContextPanel}
            aria-label={contextPanelOpen ? 'Close context panel' : 'Open context panel'}
          >
            {contextPanelOpen ? (
              <PanelRightClose className="w-4 h-4" />
            ) : (
              <PanelRightOpen className="w-4 h-4" />
            )}
          </Button>
        </div>

        {/* Message thread or welcome */}
        {!activeConversationId ? (
          <WelcomeScreen onNewConversation={handleNewConversation} />
        ) : (
          <>
            <ScrollArea className="flex-1">
              <div className="max-w-3xl mx-auto px-4 py-4 space-y-4">
                <AnimatePresence initial={false}>
                  {activeMessages.map((msg) => (
                    <motion.div
                      key={msg.id}
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.2 }}
                    >
                      <MessageBubble message={msg} />
                    </motion.div>
                  ))}
                </AnimatePresence>

                {isStreaming && !activeMessages.some((m) => m.isStreaming) && (
                  <StreamingIndicator text="Thinking…" />
                )}
                <div ref={messagesEndRef} />
              </div>
            </ScrollArea>

            <ChatInput onSend={handleSendMessage} disabled={isStreaming} />
          </>
        )}
      </div>

      {/* Context panel */}
      <AnimatePresence>
        {contextPanelOpen && !isMobile && (
          <motion.aside
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: 280, opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="w-[280px] flex-shrink-0 border-l border-border overflow-hidden bg-card"
          >
            <ContextPanel />
          </motion.aside>
        )}
      </AnimatePresence>
    </div>
  );
}
