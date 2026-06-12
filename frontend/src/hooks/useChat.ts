'use client';

import { useCallback } from 'react';
import { useChatStore } from '@/stores/chatStore';
import { useConsentStore } from '@/stores/consentStore';
import { api, type ChatResponseDTO } from '@/lib/api';

export function useChat() {
  const chatStore = useChatStore();
  const consentStore = useConsentStore();

  const activeConversation = chatStore.conversations.find(
    (c) => c.id === chatStore.activeConversationId
  );

  /**
   * Send a message to the RAG backend and store the response.
   * Creates a new conversation if none is active.
   */
  const sendMessage = useCallback(async (content: string): Promise<void> => {
    const store = useChatStore.getState();
    let convId = store.activeConversationId;

    // Auto-create a conversation if none is active
    if (!convId) {
      try {
        const conv = await api.conversations.create({});
        store.addConversation({
          id: conv.id,
          title: conv.title,
          lastMessage: content.slice(0, 100),
          lastMessageAt: new Date().toISOString(),
          createdAt: conv.created_at,
          messageCount: 0,
        });
        store.setActiveConversationId(conv.id);
        convId = conv.id;
      } catch (err) {
        console.error('Failed to create conversation', err);
        return;
      }
    }

    // Add user message locally (optimistic)
    const userMsgId = `msg-${Date.now()}`;
    store.addMessage({
      id: userMsgId,
      conversationId: convId,
      role: 'user',
      content,
      citations: [],
      createdAt: new Date().toISOString(),
    });

    // Update conversation title from first message
    const conv = store.conversations.find((c) => c.id === convId);
    if (conv && conv.title === 'New conversation') {
      store.renameConversation(
        convId,
        content.slice(0, 50) + (content.length > 50 ? '…' : ''),
      );
    }

    // Call the backend
    store.setStreaming(true);
    try {
      const profileKey = consentStore.profileMode?.toLowerCase() ?? null;
      const result: ChatResponseDTO = await api.chat.send({
        question: content,
        conversation_id: convId,
        profile_key: profileKey,
      });

      // Add assistant message with rich source metadata
      store.addMessage({
        id: result.message_id,
        conversationId: result.conversation_id,
        role: 'assistant',
        content: result.answer,
        citations: result.sources.map((s) => ({
          id: s.id,
          sourceId: s.source_id,
          source: {
            id: s.source_id,
            title: s.source_title,
            type: s.source_type as any,
            authors: s.authors,
            publicationDate: s.publication_date ?? null,
            publisher: s.publisher ?? null,
            url: s.url || '',
            doi: s.doi || null,
            language: s.language ?? null,
            description: s.description ?? null,
            tags: s.tags ?? [],
            contentSensitivity: (s.content_sensitivity as any) ?? 'low',
            internalNotes: null,
            status: 'indexed' as any,
            errorMessage: null,
            chunkCount: 0,
          },
          excerpt: s.excerpt,
          number: s.number,
        })),
        createdAt: new Date().toISOString(),
      });
    } catch (err) {
      console.error('Chat API error', err);
      store.addMessage({
        id: `msg-${Date.now() + 1}`,
        conversationId: convId,
        role: 'assistant',
        content: 'Sorry, something went wrong. Please try again.',
        citations: [],
        createdAt: new Date().toISOString(),
      });
    } finally {
      store.setStreaming(false);
    }
  }, [consentStore.profileMode]);

  /**
   * Load conversations from the backend into the store.
   */
  const loadConversations = useCallback(async () => {
    try {
      const res = await api.conversations.list();
      chatStore.setConversations(
        res.conversations.map((c) => ({
          id: c.id,
          title: c.title,
          lastMessage: c.last_message ?? null,
          lastMessageAt: c.last_message_at ?? c.created_at,
          createdAt: c.created_at,
          messageCount: c.message_count,
        })),
      );
    } catch (err) {
      console.error('Failed to load conversations', err);
    }
  }, [chatStore]);

  /**
   * Load messages for a specific conversation.
   */
  const loadMessages = useCallback(async (conversationId: string) => {
    try {
      const conv = await api.conversations.get(conversationId);
      chatStore.setMessages(
        conv.messages.map((m) => ({
          id: m.id,
          conversationId: m.conversation_id,
          role: m.role,
          content: m.content,
          citations: m.citations.map((c) => ({
            id: c.id,
            sourceId: c.source_id,
            source: { authors: [], tags: [] } as any,
            excerpt: c.excerpt,
            number: c.number,
          })),
          createdAt: m.created_at,
          isStreaming: false,
        })),
      );
    } catch (err) {
      console.error('Failed to load messages', err);
    }
  }, [chatStore]);

  return {
    ...chatStore,
    activeConversation,
    privacyMode: consentStore.profileMode,
    /** Send a message and get a RAG response */
    sendMessage,
    /** Fetch conversation list from the backend */
    loadConversations,
    /** Fetch messages for a conversation */
    loadMessages,
  };
}
