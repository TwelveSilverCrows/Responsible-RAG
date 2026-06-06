import { Source } from './source';

export interface Message {
  id: string;
  conversationId: string;
  role: 'user' | 'assistant';
  content: string;
  citations: Citation[];
  createdAt: string;
  isStreaming?: boolean;
}

export interface Citation {
  id: string;
  sourceId: string;
  source: Source;
  excerpt: string;
  number: number;
}

export interface Conversation {
  id: string;
  title: string;
  lastMessage: string | null;
  lastMessageAt: string;
  createdAt: string;
  messageCount: number;
}

export interface ChatState {
  conversations: Conversation[];
  activeConversationId: string | null;
  messages: Message[];
  isStreaming: boolean;
  sidebarOpen: boolean;
  contextPanelOpen: boolean;
}
