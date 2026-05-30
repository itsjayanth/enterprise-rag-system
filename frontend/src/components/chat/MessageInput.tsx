"use client";

import { useRef, useState } from "react";
import { Send } from "lucide-react";
import { cn } from "@/lib/utils";

interface Props {
  onSend: (text: string) => void;
  disabled?: boolean;
}

export default function MessageInput({ onSend, disabled }: Props) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  function submit() {
    const text = value.trim();
    if (!text || disabled) return;
    onSend(text);
    setValue("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  }

  function handleInput(e: React.ChangeEvent<HTMLTextAreaElement>) {
    setValue(e.target.value);
    const ta = textareaRef.current;
    if (ta) { ta.style.height = "auto"; ta.style.height = `${ta.scrollHeight}px`; }
  }

  return (
    <div className="flex items-end gap-2 rounded-xl border border-gray-200 bg-white px-4 py-3 shadow-sm">
      <textarea
        ref={textareaRef}
        rows={1}
        value={value}
        onChange={handleInput}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        placeholder="Ask a question… (Enter to send, Shift+Enter for newline)"
        className={cn(
          "flex-1 resize-none rounded-xl border border-gray-200 bg-gray-50 px-4 py-2.5 text-sm outline-none transition focus:border-blue-400 focus:ring-1 focus:ring-blue-300",
          disabled && "opacity-50 cursor-not-allowed"
        )}
      />
      <button
        onClick={submit}
        disabled={!value.trim() || disabled}
        className={cn(
          "flex h-9 w-9 shrink-0 items-center justify-center rounded-xl text-white transition",
          value.trim() && !disabled ? "bg-blue-600 hover:bg-blue-700" : "bg-gray-300 cursor-not-allowed"
        )}
      >
        <Send className="h-4 w-4" />
      </button>
    </div>
  );
}

