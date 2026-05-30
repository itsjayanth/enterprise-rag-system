"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { RefreshCw, FileText, CheckCircle, Clock, Loader2, XCircle } from "lucide-react";
import { getDocuments, type Document } from "@/lib/api/documents";
import { cn } from "@/lib/utils";

const TERMINAL = ["completed", "failed"];
const POLL_MS = 4000;

interface Props {
  refresh: number; // bump this to trigger an immediate refresh
  onSelectDocument?: (id: string, selected: boolean) => void;
  selectedIds?: Set<string>;
}

function statusIcon(status: string) {
  switch (status) {
    case "completed": return <CheckCircle className="h-4 w-4 text-green-500" />;
    case "failed":    return <XCircle className="h-4 w-4 text-red-500" />;
    case "processing":
    case "chunked":
    case "embedded":  return <Loader2 className="h-4 w-4 animate-spin text-blue-500" />;
    default:          return <Clock className="h-4 w-4 text-gray-400" />;
  }
}

function statusColor(status: string) {
  if (status === "completed") return "text-green-700 bg-green-50 border-green-200";
  if (status === "failed") return "text-red-700 bg-red-50 border-red-200";
  if (["processing","chunked","embedded","queued"].includes(status)) return "text-blue-700 bg-blue-50 border-blue-200";
  return "text-gray-600 bg-gray-50 border-gray-200";
}

export default function DocumentList({ refresh, onSelectDocument, selectedIds }: Props) {
  const [docs, setDocs] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchDocs = useCallback(async () => {
    try {
      const data = await getDocuments();
      setDocs(data);
    } catch {
      // keep stale data, silent
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchDocs(); }, [fetchDocs, refresh]);

  useEffect(() => {
    const anyPending = docs.some((d) => !TERMINAL.includes(d.status));
    if (anyPending) {
      timerRef.current = setInterval(fetchDocs, POLL_MS);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
    }
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, [docs, fetchDocs]);

  if (loading) return <p className="text-sm text-gray-500">Loading documents…</p>;
  if (docs.length === 0) return <p className="text-sm text-gray-500">No documents yet. Upload one above.</p>;

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <h2 className="flex items-center gap-2 text-lg font-semibold text-gray-800">
          <FileText className="h-5 w-5 text-blue-500" /> Documents ({docs.length})
        </h2>
        <button onClick={fetchDocs} title="Refresh" className="rounded p-1 hover:bg-gray-100">
          <RefreshCw className="h-4 w-4 text-gray-500" />
        </button>
      </div>

      {docs.map((doc) => (
        <div
          key={doc.id}
          onClick={() => onSelectDocument?.(doc.id, !(selectedIds?.has(doc.id)))}
          className={cn(
            "flex cursor-pointer items-center justify-between rounded-lg border bg-white px-4 py-3 text-sm shadow-sm transition hover:border-blue-300",
            selectedIds?.has(doc.id) && "border-blue-500 ring-1 ring-blue-400"
          )}
        >
          <div className="flex items-center gap-3 overflow-hidden">
            {statusIcon(doc.status)}
            <div className="min-w-0">
              <p className="truncate font-medium text-gray-800">{doc.filename}</p>
              <p className="text-xs text-gray-400">
                {doc.file_type.toUpperCase()} · {(doc.file_size / 1024).toFixed(1)} KB
                {doc.total_chunks != null && ` · ${doc.total_chunks} chunks`}
              </p>
            </div>
          </div>
          <span className={cn("ml-4 shrink-0 rounded border px-2 py-0.5 text-xs font-medium capitalize", statusColor(doc.status))}>
            {doc.status}
          </span>
        </div>
      ))}
    </div>
  );
}

