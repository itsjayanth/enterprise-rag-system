"use client";

import { useState } from "react";
import Link from "next/link";
import { MessageCircle } from "lucide-react";
import DocumentUpload from "@/components/documents/DocumentUpload";
import DocumentList from "@/components/documents/DocumentList";
import type { Document } from "@/lib/api/documents";

export default function HomePage() {
  const [refresh, setRefresh] = useState(0);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  function handleUploaded(_doc: Document) {
    setRefresh((n) => n + 1);
  }

  function handleSelectDocument(id: string, selected: boolean) {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (selected) next.add(id); else next.delete(id);
      return next;
    });
  }

  return (
    <main className="mx-auto max-w-3xl space-y-6 px-4 py-10">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Enterprise RAG</h1>
          <p className="text-sm text-gray-500">Upload documents, then ask questions about them.</p>
        </div>
        <Link
          href="/chat"
          className="flex items-center gap-2 rounded-xl bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 transition"
        >
          <MessageCircle className="h-4 w-4" /> Chat
          {selectedIds.size > 0 && (
            <span className="rounded-full bg-white/20 px-1.5 py-0.5 text-xs">{selectedIds.size}</span>
          )}
        </Link>
      </div>

      <DocumentUpload onUploaded={handleUploaded} />
      <DocumentList
        refresh={refresh}
        onSelectDocument={handleSelectDocument}
        selectedIds={selectedIds}
      />

      {selectedIds.size > 0 && (
        <div className="rounded-xl bg-blue-50 border border-blue-200 px-4 py-3 text-sm text-blue-700">
          {selectedIds.size} document{selectedIds.size > 1 ? "s" : ""} selected — go to{" "}
          <Link href={`/chat?docs=${[...selectedIds].join(",")}`} className="underline font-medium">
            Chat
          </Link>{" "}
          to ask questions about them.
        </div>
      )}
    </main>
  );
}
