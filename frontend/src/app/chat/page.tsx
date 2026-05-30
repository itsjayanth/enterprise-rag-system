"use client";

import { Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import ChatInterface from "@/components/chat/ChatInterface";

function ChatPage() {
  const params = useSearchParams();
  const docsParam = params.get("docs");
  const documentIds = docsParam ? docsParam.split(",").filter(Boolean) : [];

  return (
    <div className="flex h-dvh min-h-0 flex-col bg-gradient-to-b from-slate-50 to-slate-100">
      <header className="flex items-center gap-3 border-b border-gray-200 bg-white/95 px-4 py-3 shadow-sm backdrop-blur">
        <Link href="/" className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-800 transition">
          <ArrowLeft className="h-4 w-4" /> Documents
        </Link>
        <div className="h-4 w-px bg-gray-200" />
        <h1 className="text-sm font-semibold text-gray-800">
          {documentIds.length > 0
            ? `Chat (${documentIds.length} doc${documentIds.length > 1 ? "s" : ""})`
            : "Chat — all documents"}
        </h1>
      </header>
      <div className="flex min-h-0 flex-1 overflow-hidden px-4 py-4 sm:px-6 sm:py-6">
        <div className="flex min-h-0 flex-1 overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-lg">
          <ChatInterface documentIds={documentIds} />
        </div>
      </div>
    </div>
  );
}

export default function ChatPageWrapper() {
  return (
    <Suspense>
      <ChatPage />
    </Suspense>
  );
}

