'use client';

import { useChatStore } from '@/stores/chatStore';
import { useConsentStore } from '@/stores/consentStore';

export function useChat() {
  const chatStore = useChatStore();
  const consentStore = useConsentStore();

  const activeConversation = chatStore.conversations.find(
    (c) => c.id === chatStore.activeConversationId
  );

  return {
    ...chatStore,
    activeConversation,
    privacyMode: consentStore.profileMode,
  };
}
