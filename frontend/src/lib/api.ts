/**
 * lib/api.ts — Thin fetch wrapper for the RAG backend API
 * =========================================================
 * Every function returns parsed JSON or throws on error.
 * Auth tokens are read from localStorage (set after login).
 *
 * Usage:
 *   import { api } from '@/lib/api';
 *   const res = await api.chat.send("What is RAG?");
 */

// ── Helpers ────────────────────────────────────────────────────────────────

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

function getHeaders(): Record<string, string> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  // TODO: Read actual token from auth store after login is implemented
  // const token = useAuthStore.getState().token;
  // if (token) headers['Authorization'] = `Bearer ${token}`;
  return headers;
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
): Promise<T> {
  const url = `${BASE_URL}${path}`;
  const res = await fetch(url, {
    method,
    headers: getHeaders(),
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }

  return res.json();
}

// ── Types (mirroring the backend Pydantic schemas in camelCase) ────────────

export interface CitationDTO {
  id: string;
  source_id: string;
  excerpt: string;
  number: number;
}

export interface ChatRequestDTO {
  question: string;
  conversation_id?: string | null;
  profile_key?: string | null;
}

export interface ChatResponseDTO {
  answer: string;
  sources: CitationDTO[];
  conversation_id: string;
  message_id: string;
  profile_key?: string | null;
}

export interface ConversationListItemDTO {
  id: string;
  title: string;
  last_message?: string | null;
  last_message_at?: string | null;
  created_at: string;
  message_count: number;
}

export interface ConversationListResponseDTO {
  conversations: ConversationListItemDTO[];
  total: number;
  page: number;
  limit: number;
}

export interface CreateConversationDTO {
  title?: string | null;
  profile_key?: string | null;
}

export interface ConversationResponseDTO {
  id: string;
  title: string;
  profile_key?: string | null;
  messages: MessageDTO[];
  message_count: number;
  created_at: string;
  updated_at: string;
}

export interface MessageDTO {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant';
  content: string;
  citations: CitationDTO[];
  is_streaming: boolean;
  created_at: string;
}

// ── API methods ────────────────────────────────────────────────────────────

export const api = {
  /** Health check */
  health: {
    ping: () => request<{ status: string }>('GET', '/health'),
  },

  /** Chat / RAG */
  chat: {
    /** Send a question and get a RAG answer back */
    send: (body: ChatRequestDTO) =>
      request<ChatResponseDTO>('POST', '/chat', body),
  },

  /** Conversations */
  conversations: {
    /** List the user's conversations */
    list: (page = 1, limit = 20) =>
      request<ConversationListResponseDTO>(
        'GET', `/chat/conversations?page=${page}&limit=${limit}`,
      ),

    /** Create a new conversation */
    create: (body: CreateConversationDTO = {}) =>
      request<ConversationResponseDTO>('POST', '/chat/conversations', body),

    /** Get a conversation with all its messages */
    get: (id: string) =>
      request<ConversationResponseDTO>('GET', `/chat/conversations/${id}`),

    /** Rename a conversation */
    rename: (id: string, title: string) =>
      request<ConversationResponseDTO>('PUT', `/chat/conversations/${id}`, { title }),

    /** Delete a conversation */
    delete: (id: string) =>
      request<{ status: string }>('DELETE', `/chat/conversations/${id}`),
  },
};
