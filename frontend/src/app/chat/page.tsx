'use client';

import { useEffect } from 'react';
import { AppShell } from '@/components/layout/AppShell';
import { ChatContainer } from '@/components/chat/ChatContainer';
import { useChatStore } from '@/stores/chatStore';
import { AuthGuard } from '@/components/AuthGuard';

export default function ChatPage() {
  const { setActiveConversationId } = useChatStore();

  useEffect(() => {
    setActiveConversationId(null);
  }, [setActiveConversationId]);

  return (
    <AuthGuard>
      <AppShell>
        <ChatContainer />
      </AppShell>
    </AuthGuard>
  );
}
