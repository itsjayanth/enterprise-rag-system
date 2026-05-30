"use client";

import { useRef, useState } from "react";
import { Upload, FileText, AlertCircle, CheckCircle } from "lucide-react";
import { uploadDocument, type Document } from "@/lib/api/documents";
import { cn } from "@/lib/utils";

interface Props {
  onUploaded: (doc: Document) => void;
}

const MAX_SIZE_MB = 50;
const ALLOWED_TYPES = ["application/pdf", "text/plain"];
const ALLOWED_EXT = [".pdf", ".txt"];

export default function DocumentUpload({ onUploaded }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  function validate(file: File): string | null {
    const ext = "." + file.name.split(".").pop()?.toLowerCase();
    if (!ALLOWED_EXT.includes(ext)) return "Only .pdf and .txt files are allowed.";
    if (file.size > MAX_SIZE_MB * 1024 * 1024) return `Max file size is ${MAX_SIZE_MB} MB.`;
    if (file.size === 0) return "File is empty.";
    return null;
  }

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    setError(null);
    setSuccess(null);
    const file = e.target.files?.[0] ?? null;
    if (!file) return;
    const err = validate(file);
    if (err) { setError(err); return; }
    setSelectedFile(file);
  }

  async function handleUpload() {
    if (!selectedFile) return;
    setError(null);
    setSuccess(null);
    setUploading(true);
    setProgress(0);
    try {
      const doc = await uploadDocument(selectedFile, setProgress);
      setSuccess(`"${doc.filename}" uploaded — processing in background.`);
      setSelectedFile(null);
      if (inputRef.current) inputRef.current.value = "";
      onUploaded(doc);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Upload failed.";
      setError(msg);
    } finally {
      setUploading(false);
      setProgress(0);
    }
  }

  return (
    <div className="rounded-xl border border-dashed border-gray-300 bg-white p-6 shadow-sm">
      <h2 className="mb-4 flex items-center gap-2 text-lg font-semibold text-gray-800">
        <Upload className="h-5 w-5 text-blue-500" /> Upload Document
      </h2>

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <label className="flex-1 cursor-pointer rounded-lg border border-gray-200 bg-gray-50 px-4 py-2 text-sm text-gray-600 hover:bg-gray-100">
          <input
            ref={inputRef}
            type="file"
            accept=".pdf,.txt"
            className="hidden"
            onChange={handleFileChange}
            disabled={uploading}
          />
          {selectedFile ? (
            <span className="flex items-center gap-2">
              <FileText className="h-4 w-4 text-blue-500" />
              {selectedFile.name}
            </span>
          ) : (
            "Choose a PDF or TXT file…"
          )}
        </label>

        <button
          onClick={handleUpload}
          disabled={!selectedFile || uploading}
          className={cn(
            "rounded-lg px-5 py-2 text-sm font-medium text-white transition",
            selectedFile && !uploading
              ? "bg-blue-600 hover:bg-blue-700"
              : "cursor-not-allowed bg-gray-300"
          )}
        >
          {uploading ? `Uploading ${progress}%…` : "Upload"}
        </button>
      </div>

      {uploading && (
        <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-gray-200">
          <div
            className="h-full bg-blue-500 transition-all"
            style={{ width: `${progress}%` }}
          />
        </div>
      )}

      {error && (
        <p className="mt-3 flex items-center gap-1.5 text-sm text-red-600">
          <AlertCircle className="h-4 w-4" /> {error}
        </p>
      )}
      {success && (
        <p className="mt-3 flex items-center gap-1.5 text-sm text-green-600">
          <CheckCircle className="h-4 w-4" /> {success}
        </p>
      )}
    </div>
  );
}

