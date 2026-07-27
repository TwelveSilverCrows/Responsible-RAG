import { create } from 'zustand';
import type { Conversation, Message } from '@/types/chat';

interface ChatStore {
  conversations: Conversation[];
  activeConversationId: string | null;
  messages: Message[];
  isStreaming: boolean;
  sidebarOpen: boolean;
  contextPanelOpen: boolean;

  setConversations: (conversations: Conversation[]) => void;
  setActiveConversationId: (id: string | null) => void;
  setMessages: (messages: Message[]) => void;
  addMessage: (message: Message) => void;
  updateMessage: (id: string, updates: Partial<Message>) => void;
  setStreaming: (streaming: boolean) => void;
  toggleSidebar: () => void;
  toggleContextPanel: () => void;
  addConversation: (conversation: Conversation) => void;
  removeConversation: (id: string) => void;
  renameConversation: (id: string, title: string) => void;
}

export const useChatStore = create<ChatStore>()((set) => ({
  conversations: [],
  activeConversationId: null,
  messages: [],
  isStreaming: false,
  sidebarOpen: true,
  contextPanelOpen: false,

  setConversations: (conversations) => set({ conversations }),
  setActiveConversationId: (id) => set({ activeConversationId: id }),
  setMessages: (messages) => set({ messages }),
  addMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),
  updateMessage: (id, updates) =>
    set((state) => ({
      messages: state.messages.map((m) => (m.id === id ? { ...m, ...updates } : m)),
    })),
  setStreaming: (isStreaming) => set({ isStreaming }),
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  toggleContextPanel: () => set((state) => ({ contextPanelOpen: !state.contextPanelOpen })),
  addConversation: (conversation) =>
    set((state) => ({ conversations: [conversation, ...state.conversations] })),
  removeConversation: (id) =>
    set((state) => ({
      conversations: state.conversations.filter((c) => c.id !== id),
      activeConversationId: state.activeConversationId === id ? null : state.activeConversationId,
    })),
  renameConversation: (id, title) =>
    set((state) => ({
      conversations: state.conversations.map((c) => (c.id === id ? { ...c, title } : c)),
    })),
}));
