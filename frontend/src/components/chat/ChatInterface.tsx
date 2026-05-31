"use client";

import { useState } from "react";
import MessageList, { type Message } from "./MessageList";
import MessageInput from "./MessageInput";
import { streamChatQuery, type ChatSource } from "@/lib/api/chat";

// crypto.randomUUID shim for environments that don't have it
function newId() {
  if (typeof crypto !== "undefined" && crypto.randomUUID) return crypto.randomUUID();
  return Math.random().toString(36).slice(2);
}

interface Props {
  documentIds?: string[];
}

export default function ChatInterface({ documentIds }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [streaming, setStreaming] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [statusText, setStatusText] = useState<string | null>(null);

  async function handleSend(query: string) {
    if (streaming) return;

    const userMsg: Message = { id: newId(), role: "user", content: query };
    const assistantId = newId();
    const assistantMsg: Message = { id: assistantId, role: "assistant", content: "", streaming: true };
    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    setStreaming(true);
    setStatusText(null);

    try {
      const gen = streamChatQuery({
        query,
        session_id: sessionId,
        document_ids: documentIds && documentIds.length > 0 ? documentIds : null,
      });

      for await (const event of gen) {
        if (event.type === "status") {
          setStatusText(String(event.data.message ?? ""));
        } else if (event.type === "token") {
          const token = String(event.data.token ?? "");
          setMessages((prev) =>
            prev.map((m) => m.id === assistantId ? { ...m, content: m.content + token } : m)
          );
        } else if (event.type === "sources") {
          const sources = event.data.sources as ChatSource[];
          setMessages((prev) =>
            prev.map((m) => m.id === assistantId ? { ...m, sources } : m)
          );
        } else if (event.type === "done") {
          const sid = event.data.session_id as string | undefined;
          if (sid) setSessionId(sid);
          setMessages((prev) =>
            prev.map((m) => m.id === assistantId ? { ...m, streaming: false } : m)
          );
        } else if (event.type === "error") {
          setMessages((prev) =>
            prev.map((m) => m.id === assistantId ? { ...m, content: `Error: ${event.data.message}`, streaming: false } : m)
          );
        }
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Unknown error";
      setMessages((prev) =>
        prev.map((m) => m.id === assistantId ? { ...m, content: `Error: ${msg}`, streaming: false } : m)
      );
    } finally {
      setStreaming(false);
      setStatusText(null);
    }
  }

  return (
    <div className="flex h-full min-h-0 flex-col">
      {statusText && (
        <div className="border-b border-blue-100 bg-blue-50 px-4 py-2 text-xs text-blue-600">
          {statusText}…
        </div>
      )}
      <MessageList messages={messages} />
      <div className="shrink-0 border-t border-gray-200 bg-white px-4 pb-4 pt-3">
        <MessageInput onSend={handleSend} disabled={streaming} />
      </div>
    </div>
  );
}

