# Frontend Stack & Architecture - Enterprise RAG System

## Executive Summary

This document defines the **frontend architecture** for the enterprise RAG platform, covering Next.js 14+, streaming chat UI, file uploads, authentication, and modern development practices.

---

## 1. Technology Stack

### **1.1 Core Framework: Next.js 14+**

**Why Next.js 14:**

✅ **App Router** - Modern React Server Components
✅ **Streaming SSR** - Perfect for streaming chat responses
✅ **Server Actions** - Simplified data mutations
✅ **Built-in optimizations** - Image optimization, font optimization
✅ **API routes** - BFF (Backend-for-Frontend) pattern
✅ **Edge runtime** - Fast global deployment
✅ **Best DX** - TypeScript, Hot reload, Fast Refresh

**Alternatives considered:**
- **SvelteKit**: Lighter but smaller ecosystem
- **React SPA**: No SSR benefits, worse SEO
- **Remix**: Good but smaller community

### **1.2 UI Component Library: shadcn/ui + Radix UI**

**Why shadcn/ui:**

✅ **Copy-paste components** - No black box dependencies
✅ **Customizable** - Full control over styling
✅ **Accessible** - Built on Radix UI (WAI-ARIA compliant)
✅ **Modern** - TailwindCSS + TypeScript
✅ **Production-ready** - Used by Vercel, Linear, etc.

**Components we'll use:**
- Button, Input, Card, Dialog, Sheet
- Select, Dropdown Menu, Tooltip
- Toast (notifications)
- Skeleton (loading states)
- Progress bar (file upload)

### **1.3 Styling: TailwindCSS**

**Why Tailwind:**

✅ **Utility-first** - Fast development
✅ **Consistent design system** - Design tokens
✅ **Small bundle size** - JIT compiler, tree-shaking
✅ **Responsive** - Mobile-first breakpoints
✅ **Dark mode** - Built-in support

### **1.4 State Management: Zustand**

**Why Zustand over Redux:**

✅ **Minimal boilerplate** - 10x less code
✅ **Simple API** - Easy to learn
✅ **TypeScript-first** - Great type inference
✅ **No Context providers** - Cleaner component tree
✅ **DevTools** - Redux DevTools compatible

**Stores:**
- `authStore` - User authentication state
- `chatStore` - Chat sessions and messages
- `documentStore` - Document list and uploads
- `uiStore` - UI state (sidebar, modals, etc.)

### **1.5 Data Fetching: React Query (TanStack Query)**

**Why React Query:**

✅ **Automatic caching** - Reduces API calls
✅ **Background refetching** - Fresh data
✅ **Optimistic updates** - Better UX
✅ **Error handling** - Retry logic
✅ **DevTools** - Debug queries

### **1.6 Forms: React Hook Form + Zod**

**Why React Hook Form:**

✅ **Performance** - Uncontrolled components
✅ **TypeScript** - Full type safety
✅ **Validation** - Integrated with Zod
✅ **Small bundle** - 9KB gzipped

**Why Zod:**

✅ **Schema validation** - Type-safe
✅ **Reusable schemas** - Frontend + Backend
✅ **Error messages** - Clear validation errors

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    NEXT.JS APP                          │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │            App Router (src/app/)                  │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌──────────┐ │ │
│  │  │   /login    │  │   /chat     │  │ /docs    │ │ │
│  │  │   page.tsx  │  │  page.tsx   │  │page.tsx  │ │ │
│  │  └─────────────┘  └─────────────┘  └──────────┘ │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │         Components (src/components/)              │ │
│  │  ┌──────────────┐  ┌──────────────┐             │ │
│  │  │ ChatInterface│  │DocumentUpload│             │ │
│  │  │ (streaming)  │  │  (progress)  │             │ │
│  │  └──────────────┘  └──────────────┘             │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │            State (src/lib/stores/)                │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐       │ │
│  │  │authStore │  │chatStore │  │ docStore │       │ │
│  │  └──────────┘  └──────────┘  └──────────┘       │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │          API Client (src/lib/api/)                │ │
│  │  - Axios instance                                 │ │
│  │  - SSE streaming client                           │ │
│  │  - Auth interceptors                              │ │
│  └───────────────────────────────────────────────────┘ │
│                         │                               │
└─────────────────────────┼───────────────────────────────┘
                          │ HTTP/SSE
                          ▼
               ┌─────────────────────┐
               │   API Gateway       │
               │   (Backend)         │
               └─────────────────────┘
```

---

## 3. Key Features Implementation

### **3.1 Streaming Chat Interface**

**Component Structure:**
```typescript
// src/components/chat/ChatInterface.tsx

'use client'

import { useState } from 'react'
import { useChatStore } from '@/lib/stores/chatStore'
import { MessageList } from './MessageList'
import { MessageInput } from './MessageInput'
import { SourcesPanel } from './SourcesPanel'
import { streamChatQuery } from '@/lib/api/chat'

export function ChatInterface() {
  const { currentSession, addMessage, updateMessage } = useChatStore()
  const [isStreaming, setIsStreaming] = useState(false)
  const [sources, setSources] = useState([])

  const handleSendMessage = async (query: string) => {
    // Add user message
    const userMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: query,
      timestamp: new Date(),
    }
    addMessage(userMessage)

    // Create assistant message placeholder
    const assistantMessage = {
      id: crypto.randomUUID(),
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      streaming: true,
    }
    addMessage(assistantMessage)

    setIsStreaming(true)

    try {
      // Stream response
      for await (const event of streamChatQuery({
        query,
        session_id: currentSession?.id,
      })) {
        switch (event.type) {
          case 'status':
            // Show status indicator
            break

          case 'sources':
            setSources(event.data.sources)
            break

          case 'token':
            // Append token to message
            updateMessage(assistantMessage.id, (msg) => ({
              ...msg,
              content: msg.content + event.data.content,
            }))
            break

          case 'done':
            // Mark as complete
            updateMessage(assistantMessage.id, (msg) => ({
              ...msg,
              streaming: false,
              sources: sources,
            }))
            break

          case 'error':
            throw new Error(event.data.message)
        }
      }
    } catch (error) {
      console.error('Chat error:', error)
      // Show error toast
    } finally {
      setIsStreaming(false)
    }
  }

  return (
    <div className="flex h-[calc(100vh-200px)] gap-4">
      <div className="flex-1 flex flex-col">
        <MessageList
          messages={currentSession?.messages || []}
          isStreaming={isStreaming}
        />
        <MessageInput
          onSend={handleSendMessage}
          disabled={isStreaming}
        />
      </div>
      
      {sources.length > 0 && (
        <div className="w-80">
          <SourcesPanel sources={sources} />
        </div>
      )}
    </div>
  )
}
```

**Streaming Message Component:**
```typescript
// src/components/chat/StreamingMessage.tsx

'use client'

import { useEffect, useRef } from 'react'
import { motion } from 'framer-motion'

interface StreamingMessageProps {
  content: string
  streaming: boolean
}

export function StreamingMessage({ content, streaming }: StreamingMessageProps) {
  const endRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom while streaming
  useEffect(() => {
    if (streaming) {
      endRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [content, streaming])

  return (
    <div className="relative">
      <div className="prose prose-sm max-w-none">
        {content}
        {streaming && (
          <motion.span
            animate={{ opacity: [1, 0] }}
            transition={{ duration: 0.8, repeat: Infinity }}
            className="inline-block w-2 h-4 bg-blue-500 ml-1"
          />
        )}
      </div>
      <div ref={endRef} />
    </div>
  )
}
```

### **3.2 File Upload with Progress**

```typescript
// src/components/documents/DocumentUpload.tsx

'use client'

import { useState } from 'react'
import { useDocumentStore } from '@/lib/stores/documentStore'
import { uploadDocument } from '@/lib/api/documents'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { FileText, Upload } from 'lucide-react'
import { toast } from 'sonner'

export function DocumentUpload() {
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const { addDocument } = useDocumentStore()

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    // Validate file type
    const allowedTypes = ['application/pdf', 'text/plain']
    if (!allowedTypes.includes(file.type)) {
      toast.error('Only PDF and TXT files are supported')
      return
    }

    // Validate file size (50MB)
    if (file.size > 50 * 1024 * 1024) {
      toast.error('File size must be less than 50MB')
      return
    }

    setUploading(true)
    setProgress(0)

    try {
      const document = await uploadDocument(file, (progress) => {
        setProgress(progress)
      })

      addDocument(document)
      toast.success('Document uploaded successfully')
    } catch (error) {
      console.error('Upload error:', error)
      toast.error('Failed to upload document')
    } finally {
      setUploading(false)
      setProgress(0)
    }
  }

  return (
    <div className="border-2 border-dashed border-gray-300 rounded-lg p-8">
      {uploading ? (
        <div className="space-y-4">
          <div className="flex items-center justify-center">
            <FileText className="w-12 h-12 text-blue-500 animate-pulse" />
          </div>
          <p className="text-center text-sm text-gray-600">
            Uploading... {progress}%
          </p>
          <Progress value={progress} className="w-full" />
        </div>
      ) : (
        <label className="cursor-pointer flex flex-col items-center">
          <Upload className="w-12 h-12 text-gray-400 mb-4" />
          <span className="text-sm text-gray-600 mb-2">
            Click to upload or drag and drop
          </span>
          <span className="text-xs text-gray-500">
            PDF or TXT (Max 50MB)
          </span>
          <input
            type="file"
            className="hidden"
            accept=".pdf,.txt"
            onChange={handleFileChange}
          />
        </label>
      )}
    </div>
  )
}
```

**Upload API Client:**
```typescript
// src/lib/api/documents.ts

import apiClient from './client'

export async function uploadDocument(
  file: File,
  onProgress?: (progress: number) => void
) {
  const formData = new FormData()
  formData.append('file', file)

  const response = await apiClient.post('/api/v1/documents/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      const progress = Math.round(
        (progressEvent.loaded * 100) / (progressEvent.total || 1)
      )
      onProgress?.(progress)
    },
  })

  return response.data
}

export async function getDocuments() {
  const response = await apiClient.get('/api/v1/documents')
  return response.data
}

export async function deleteDocument(id: string) {
  await apiClient.delete(`/api/v1/documents/${id}`)
}
```

### **3.3 Authentication**

**Auth Store:**
```typescript
// src/lib/stores/authStore.ts

import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface User {
  id: string
  email: string
  full_name: string
}

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  checkAuth: () => boolean
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,

      login: async (email: string, password: string) => {
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/api/v1/auth/login`,
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password }),
          }
        )

        if (!response.ok) {
          throw new Error('Login failed')
        }

        const data = await response.json()

        set({
          user: data.user,
          token: data.token,
          isAuthenticated: true,
        })

        localStorage.setItem('auth_token', data.token)
      },

      logout: () => {
        set({
          user: null,
          token: null,
          isAuthenticated: false,
        })
        localStorage.removeItem('auth_token')
      },

      checkAuth: () => {
        const token = localStorage.getItem('auth_token')
        return !!token && get().isAuthenticated
      },
    }),
    {
      name: 'auth-storage',
    }
  )
)
```

**Protected Route Middleware:**
```typescript
// src/middleware.ts

import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function middleware(request: NextRequest) {
  const token = request.cookies.get('auth_token')?.value
  const isAuthPage = request.nextUrl.pathname.startsWith('/login')

  if (!token && !isAuthPage) {
    return NextResponse.redirect(new URL('/login', request.url))
  }

  if (token && isAuthPage) {
    return NextResponse.redirect(new URL('/chat', request.url))
  }

  return NextResponse.next()
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
}
```

### **3.4 Chat Store**

```typescript
// src/lib/stores/chatStore.ts

import { create } from 'zustand'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: Source[]
  timestamp: Date
  streaming?: boolean
}

interface ChatSession {
  id: string
  title: string
  messages: Message[]
  created_at: Date
}

interface ChatState {
  sessions: ChatSession[]
  currentSession: ChatSession | null
  
  createSession: () => void
  selectSession: (id: string) => void
  addMessage: (message: Message) => void
  updateMessage: (id: string, updater: (msg: Message) => Message) => void
  loadSessions: () => Promise<void>
}

export const useChatStore = create<ChatState>((set, get) => ({
  sessions: [],
  currentSession: null,

  createSession: () => {
    const newSession: ChatSession = {
      id: crypto.randomUUID(),
      title: 'New Chat',
      messages: [],
      created_at: new Date(),
    }
    set((state) => ({
      sessions: [newSession, ...state.sessions],
      currentSession: newSession,
    }))
  },

  selectSession: (id: string) => {
    const session = get().sessions.find((s) => s.id === id)
    if (session) {
      set({ currentSession: session })
    }
  },

  addMessage: (message: Message) => {
    set((state) => {
      if (!state.currentSession) return state

      return {
        currentSession: {
          ...state.currentSession,
          messages: [...state.currentSession.messages, message],
        },
      }
    })
  },

  updateMessage: (id: string, updater: (msg: Message) => Message) => {
    set((state) => {
      if (!state.currentSession) return state

      return {
        currentSession: {
          ...state.currentSession,
          messages: state.currentSession.messages.map((msg) =>
            msg.id === id ? updater(msg) : msg
          ),
        },
      }
    })
  },

  loadSessions: async () => {
    // Load from API
    const response = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL}/api/v1/chat/sessions`,
      {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('auth_token')}`,
        },
      }
    )
    const sessions = await response.json()
    set({ sessions })
  },
}))
```

---

## 4. Performance Optimization

### **4.1 Code Splitting**

```typescript
// Lazy load heavy components
import dynamic from 'next/dynamic'

const MarkdownRenderer = dynamic(() => import('@/components/MarkdownRenderer'), {
  loading: () => <div>Loading...</div>,
})

const PdfViewer = dynamic(() => import('@/components/PdfViewer'), {
  ssr: false, // Don't SSR PDF viewer
})
```

### **4.2 Image Optimization**

```typescript
import Image from 'next/image'

<Image
  src="/logo.png"
  alt="Logo"
  width={200}
  height={50}
  priority // Load immediately
/>
```

### **4.3 Caching Strategy**

```typescript
// src/lib/api/cache.ts

import { QueryClient } from '@tanstack/react-query'

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})
```

---

## 5. Deployment

### **5.1 Dockerfile (Production)**

```dockerfile
# frontend/Dockerfile

FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --only=production

FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV NEXT_TELEMETRY_DISABLED 1
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs
EXPOSE 3000
ENV PORT 3000

CMD ["node", "server.js"]
```

### **5.2 Environment Variables**

```bash
# .env.local (development)
NEXT_PUBLIC_API_URL=http://localhost:8000

# .env.production
NEXT_PUBLIC_API_URL=https://api.enterprise-rag.com
```

---

## Summary

This frontend architecture provides:

- ✅ **Modern React** with Next.js 14 App Router
- ✅ **Streaming UI** for real-time chat
- ✅ **File uploads** with progress tracking
- ✅ **Authentication** with JWT
- ✅ **State management** with Zustand
- ✅ **Accessible UI** with shadcn/ui
- ✅ **Type-safe** with TypeScript
- ✅ **Performant** with optimizations
- ✅ **Production-ready** deployment

**Tech Stack Summary:**
- **Framework:** Next.js 14+
- **UI:** shadcn/ui + Radix UI
- **Styling:** TailwindCSS
- **State:** Zustand
- **Data Fetching:** React Query
- **Forms:** React Hook Form + Zod
- **Deployment:** Docker + Kubernetes

---

**Document Version:** 1.0  
**Last Updated:** 2026-05-25  
**Owner:** Frontend Team

