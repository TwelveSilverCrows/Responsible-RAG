'use client';

import { useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { AppShell } from '@/components/layout/AppShell';
import { ChatContainer } from '@/components/chat/ChatContainer';
import { useChatStore } from '@/stores/chatStore';
import { AuthGuard } from '@/components/AuthGuard';

export default function ConversationPage() {
  const params = useParams<{ conversationId: string }>();
  const { setActiveConversationId, conversations } = useChatStore();

  useEffect(() => {
    if (params.conversationId) {
      const exists = conversations.some((c) => c.id === params.conversationId);
      if (exists) {
        setActiveConversationId(params.conversationId);
      }
    }
  }, [params.conversationId, setActiveConversationId, conversations]);

  return (
    <AuthGuard>
      <AppShell>
        <ChatContainer />
      </AppShell>
    </AuthGuard>
  );
}
