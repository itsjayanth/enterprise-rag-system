"use client";

import { useEffect, useRef } from "react";
import { Bot, User, BookOpen } from "lucide-react";
import { cn } from "@/lib/utils";
import type { ChatSource } from "@/lib/api/chat";

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: ChatSource[];
  streaming?: boolean;
}

interface Props {
  messages: Message[];
}

export default function MessageList({ messages }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-2 text-gray-400">
        <Bot className="h-10 w-10" />
        <p className="text-sm">Ask a question about your documents.</p>
      </div>
    );
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto px-4 py-4 pb-8">
      {messages.map((msg) => (
        <div key={msg.id} className={cn("flex gap-3", msg.role === "user" ? "justify-end" : "justify-start")}>
          {msg.role === "assistant" && (
            <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-blue-100 text-blue-600">
              <Bot className="h-4 w-4" />
            </div>
          )}
          <div className={cn("max-w-[75%] space-y-2", msg.role === "user" && "items-end")}>
            <div className={cn(
              "rounded-xl px-4 py-2.5 text-sm leading-relaxed whitespace-pre-wrap",
              msg.role === "user"
                ? "bg-blue-600 text-white rounded-br-sm"
                : "bg-white border border-gray-200 text-gray-800 rounded-bl-sm shadow-sm"
            )}>
              {msg.content || (msg.streaming ? <span className="animate-pulse">&#9608;</span> : "")}
            </div>
            {msg.sources && msg.sources.length > 0 && (
              <div className="rounded-lg border border-gray-100 bg-gray-50 px-3 py-2 text-xs text-gray-500">
                <p className="mb-1 flex items-center gap-1 font-medium text-gray-600">
                  <BookOpen className="h-3 w-3" /> Sources
                </p>
                {msg.sources.map((src, i) => (
                  <p key={i} className="truncate">
                    [{i + 1}] {src.source_file ?? src.document_id ?? "unknown"}
                    {src.page_number != null && `, p.${src.page_number}`}
                    {src.score != null && ` (score: ${Number(src.score).toFixed(2)})`}
                  </p>
                ))}
              </div>
            )}
          </div>
          {msg.role === "user" && (
            <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-gray-200 text-gray-600">
              <User className="h-4 w-4" />
            </div>
          )}
        </div>
      ))}
      <div ref={bottomRef} />
    </div>
  );
}

