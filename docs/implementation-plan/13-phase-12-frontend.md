# Phase 12: Frontend

**Goal:** Build the Next.js user interface for document upload, processing status, document-aware chat, and streamed answers with sources.

**Duration:** 5-6 hours

**Dependencies:**
- `12-phase-11-workers.md` complete

---

## 📋 Phase Objectives

By the end of this phase, you will have:

- ✅ A working Next.js 14 application structure
- ✅ Global layout and base page scaffold
- ✅ Document upload UI with progress feedback
- ✅ Document list/status view
- ✅ Streaming chat interface
- ✅ API helpers for uploads and SSE chat

---

## 📂 Files to Create or Update

```text
frontend/
├── package.json                    # already created in Phase 1
├── tsconfig.json
├── tailwind.config.ts
└── src/
    ├── app/
    │   ├── layout.tsx
    │   ├── page.tsx
    │   └── chat/
    │       └── page.tsx
    ├── components/
    │   ├── chat/
    │   │   ├── ChatInterface.tsx
    │   │   ├── MessageInput.tsx
    │   │   └── MessageList.tsx
    │   └── documents/
    │       ├── DocumentList.tsx
    │       └── DocumentUpload.tsx
    └── lib/
        └── api/
            ├── client.ts
            ├── chat.ts
            └── documents.ts
```

Optional but useful:

```text
frontend/src/lib/stores/
frontend/src/types/
frontend/src/styles/globals.css
```

---

## 🧭 UI Scope for the MVP

Keep the frontend focused on the core user journey:

1. upload one or more documents
2. watch status until processing completes
3. ask questions about the uploaded documents
4. read streamed answers with citations

Skip advanced polish for now:

- auth screens
- multi-user state
- dark mode theming
- drag-and-drop edge cases
- full session search/history UX

Those can come later once the core workflow is stable.

---

## 🏗️ Step 1: Complete the base Next.js app structure

Make sure the frontend has at least:

- `src/app/layout.tsx`
- `src/app/page.tsx`
- `src/app/chat/page.tsx`
- global CSS and Tailwind wiring

### Suggested route plan

- `/` → landing page with upload + recent docs
- `/chat` → main chat experience

You can also place everything on `/` if you want a simpler first version.

---

## 🎨 Step 2: Add styling foundation

The existing `package.json` already includes:

- Tailwind CSS
- Radix packages
- `clsx`
- `tailwind-merge`
- `lucide-react`
- `zustand`
- `axios`

### Minimum setup to finish now

- `tailwind.config.ts`
- `postcss.config.js`
- `globals.css`
- a `cn()` helper if you want composable classes

Keep the design simple and readable.

---

## 🔌 Step 3: Build API helpers

Create a small API client in `frontend/src/lib/api/client.ts`.

### Responsibilities

- set `baseURL` from `NEXT_PUBLIC_API_URL`
- provide JSON defaults
- export a shared axios instance

Then create:

### `documents.ts`

- `uploadDocument(file, onProgress?)`
- `getDocuments()`
- `getDocument(id)`

### `chat.ts`

- `streamChatQuery(payload)`
- parse SSE event stream
- yield normalized frontend events

Try to keep the stream parser isolated in one place.

---

## 📄 Step 4: Implement `DocumentUpload.tsx`

### Required behavior

- file picker for `.pdf` and `.txt`
- client-side size/type validation
- upload progress indicator
- success/failure feedback
- refresh or append document list after upload

### Good UX details

- disable controls while uploading
- show file name
- show 0-100% progress
- show processing note after upload because backend work continues asynchronously

---

## 📚 Step 5: Implement `DocumentList.tsx`

Show uploaded documents and their statuses.

### Minimum fields to render

- filename
- status
- file type
- created time
- total chunks when available

### Statuses to handle visually

- `queued`
- `processing`
- `completed`
- `failed`

### Recommended behavior

- poll periodically while any document is still processing
- stop polling when all documents are in terminal states

This makes the worker phase visible in the UI.

---

## 💬 Step 6: Implement the chat components

### `MessageList.tsx`

- renders ordered messages
- scrolls to bottom on updates
- displays assistant sources beneath relevant messages

### `MessageInput.tsx`

- textarea or single input
- submit on Enter / button click
- disabled while streaming if desired

### `ChatInterface.tsx`

- holds chat state
- sends user queries
- creates placeholder assistant message
- appends streamed tokens
- stores returned sources
- handles errors gracefully

You can manage state with:

- local component state for MVP, or
- Zustand if you want easier scaling to session-based UI

---

## 🌊 Step 7: Parse SSE on the client

Your frontend stream logic should understand these event types from the backend:

- `status`
- `token`
- `sources`
- `done`
- `error`

### Recommended client flow

1. add the user message to UI immediately
2. add an empty assistant message placeholder
3. start reading the stream
4. append token text to the assistant message as events arrive
5. attach sources when received
6. mark the assistant message complete on `done`

This is the key interaction for the whole app.

---

## 🧪 Step 8: Run and test the frontend

Start the frontend:

```bash
cd /Users/JMM9/Documents/projects/ai_specifics/enterprise-rag-system/frontend
npm install
npm run dev
```

Open:

```text
http://localhost:3000
```

### Manual user journey to verify

1. upload a PDF/TXT file
2. confirm the document appears in the list
3. wait for it to reach `completed`
4. go to the chat interface
5. ask a question grounded in the uploaded document
6. confirm the answer streams progressively
7. confirm citations/sources appear

---

## ✅ Success Criteria

This phase is complete when:

- uploads work from the browser
- document status updates are visible
- chat answers stream in real time
- sources are displayed in the UI
- the user can complete the full journey without using curl

---

## 🐛 Common Issues

### 1. Browser shows CORS errors

Check backend CORS configuration and `NEXT_PUBLIC_API_URL`.

### 2. Upload works in curl but fails in browser

Check multipart handling, request URL, and frontend file validation.

### 3. Streaming does not update progressively

The SSE parser may be buffering incorrectly. Inspect raw chunks in the browser console.

### 4. Document status never updates in UI

The polling logic may not be re-fetching documents or may be caching too aggressively.

---

## 🎯 Phase 12 Checklist

- [ ] Completed Next.js app structure
- [ ] Added Tailwind configuration and global styling
- [ ] Added shared API client
- [ ] Implemented document upload component
- [ ] Implemented document list/status view
- [ ] Implemented streaming chat UI
- [ ] Implemented SSE parsing on the client
- [ ] Verified full upload → process → chat workflow in the browser

---

## 📝 Commit Phase 12

```bash
git add .
git commit -m "feat: Phase 12 - Frontend upload and chat experience

- Added Next.js app shell and styling foundation
- Added document upload and status UI
- Added streaming chat interface
- Integrated frontend with backend upload and chat APIs"
```

---

## 🎉 Implementation Plan Complete

Once this phase passes, run a final system check:

```bash
cd /Users/JMM9/Documents/projects/ai_specifics/enterprise-rag-system
make dev
```

Then validate the complete user flow:

1. upload a document
2. wait for processing to complete
3. ask a question
4. verify grounded answer + sources

---

## ➡️ Recommended Next Work

After the full MVP is working, the most valuable follow-up improvements are:

1. authentication and multi-user isolation
2. better observability and metrics
3. semantic chunking
4. hybrid retrieval and caching
5. production deployment hardening

---

**Phase 12 Complete!**

**Status:** ✅ MVP web application ready

