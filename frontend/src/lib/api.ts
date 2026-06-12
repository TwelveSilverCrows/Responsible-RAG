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

export const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

/** Read a Bearer token from localStorage (set by the auth store). */
export function _readAuthToken(): string | undefined {
  try {
    const raw = localStorage.getItem('auth-store');
    if (raw) {
      const parsed = JSON.parse(raw);
      return parsed?.state?.token;
    }
  } catch {
    // localStorage not available or corrupt
  }
  return undefined;
}

function getHeaders(): Record<string, string> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  const token = _readAuthToken();
  if (token) headers['Authorization'] = `Bearer ${token}`;
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
  source_title: string;
  source_type: string;
  authors: string[];
  publication_date: string | null;
  publisher: string | null;
  url: string;
  doi: string;
  language: string | null;
  description: string | null;
  tags: string[];
  content_sensitivity: string;
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

// ── Auth DTOs ──────────────────────────────────────────────

export interface LoginRequestDTO {
  email: string;
  password: string;
}

export interface AuthUserDTO {
  id: string;
  email: string;
  display_name: string;
  role: 'client' | 'admin';
  email_verified: boolean;
  onboarding_completed: boolean;
  created_at: string;
}

export interface LoginResponseDTO {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: AuthUserDTO;
  is_new_user: boolean;
}

// ── API methods ────────────────────────────────────────────

export const api = {
  /** Health check */
  health: {
    ping: () => request<{ status: string }>('GET', '/health'),
  },

  /** Authentication (dev mode — dummy admin user) */
  auth: {
    /** Log in with email + password */
    login: (body: LoginRequestDTO) =>
      request<LoginResponseDTO>('POST', '/auth/login', body),

    /** Authenticate with Google access token */
    google: (accessToken: string) =>
      request<LoginResponseDTO>('POST', '/auth/google', { id_token: accessToken }),

    /** Get current user profile */
    me: () => request<AuthUserDTO>('GET', '/auth/me'),
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

  /** Admin sources management */
  sources: {
    /** List all sources */
    list: (page = 1, limit = 20, status?: string) => {
      const params = new URLSearchParams({ page: String(page), limit: String(limit) });
      if (status) params.set('status', status);
      return request<SourceListResponseDTO>('GET', `/admin/sources?${params}`);
    },

    /** Get a single source */
    get: (id: string) =>
      request<SourceResponseDTO>('GET', `/admin/sources/${id}`),

    /** Create a new source (metadata only) */
    create: (body: SourceCreateRequestDTO) =>
      request<SourceResponseDTO>('POST', '/admin/sources', body),

    /** Update source metadata */
    update: (id: string, body: SourceUpdateRequestDTO) =>
      request<SourceResponseDTO>('PUT', `/admin/sources/${id}`, body),

    /** Delete a source */
    delete: (id: string) =>
      request<{ status: string; source_id: string }>('DELETE', `/admin/sources/${id}`),

    /** Upload a file for ingestion */
    upload: async (file: File) => {
      const url = `${BASE_URL}/admin/sources/upload`;
      const formData = new FormData();
      formData.append('file', file);
      const headers: Record<string, string> = {};
      const token = _readAuthToken();
      if (token) headers['Authorization'] = `Bearer ${token}`;
      const res = await fetch(url, {
        method: 'POST',
        headers,
        body: formData,
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }
      return res.json() as Promise<UploadResponseDTO>;
    },

    /** Submit a YouTube URL for background transcription & ingestion */
    uploadYouTube: (body: YouTubeUploadRequestDTO) =>
      request<UploadResponseDTO>('POST', '/admin/sources/youtube', body),

    /** Submit a webpage URL for background scraping & ingestion */
    uploadWebpage: (body: WebPageUploadRequestDTO) =>
      request<UploadResponseDTO>('POST', '/admin/sources/webpage', body),

    /** Get dashboard stats */
    stats: () =>
      request<StatsResponseDTO>('GET', '/admin/dashboard/stats'),
  },
};

// ── Admin / Source DTOs ──────────────────────────────────────

export interface SourceResponseDTO {
  id: string;
  title: string;
  source_type: string;
  authors: string[];
  publication_date: string | null;
  publisher: string | null;
  url: string;
  doi: string | null;
  language: string | null;
  description: string | null;
  tags: string[];
  content_sensitivity: string;
  internal_notes: string | null;
  status: 'processing' | 'indexed' | 'error';
  error_message: string | null;
  chunk_count: number;
}

export interface SourceListResponseDTO {
  sources: SourceResponseDTO[];
  total: number;
  page: number;
  limit: number;
}

export interface SourceCreateRequestDTO {
  title: string;
  source_type: string;
  authors?: string[];
  publication_date?: string | null;
  publisher?: string | null;
  url: string;
  doi?: string | null;
  language?: string | null;
  description?: string | null;
  tags?: string[];
  content_sensitivity?: string;
  internal_notes?: string | null;
}

export interface SourceUpdateRequestDTO {
  title?: string;
  authors?: string[];
  publication_date?: string | null;
  publisher?: string | null;
  url?: string | null;
  doi?: string | null;
  language?: string | null;
  description?: string | null;
  tags?: string[];
  content_sensitivity?: string;
  internal_notes?: string | null;
}

export interface WebPageUploadRequestDTO {
  url: string;
  title: string;
  source_type?: string;
  authors?: string[];
  publication_date?: string | null;
  publisher?: string | null;
  language?: string | null;
  description?: string | null;
  tags?: string[];
  content_sensitivity?: string;
  internal_notes?: string | null;
}

export interface YouTubeUploadRequestDTO {
  url: string;
  title: string;
  authors?: string[];
  publication_date?: string | null;
  publisher?: string | null;
  language?: string | null;
  description?: string | null;
  tags?: string[];
  content_sensitivity?: string;
  internal_notes?: string | null;
}

export interface UploadResponseDTO {
  id: string;
  filename: string;
  source_type: string;
  status: 'processing' | 'indexed' | 'error';
  chunk_count: number;
}

export interface StatsResponseDTO {
  total_sources: number;
  indexed_sources: number;
  processing_sources: number;
  error_sources: number;
  incomplete_metadata: number;
}
