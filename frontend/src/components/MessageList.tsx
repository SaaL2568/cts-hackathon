"use client";

import type { ChatTurn } from "@/lib/types";
import LoadingIndicator from "./LoadingIndicator";
import MessageBubble from "./MessageBubble";

interface MessageListProps {
  messages: ChatTurn[];
  loading: boolean;
  emptyTitle?: string;
  emptyBody?: string;
}

export default function MessageList({
  messages,
  loading,
  emptyTitle = "No messages yet",
  emptyBody = "Ask a question about an ingested drug label to get started.",
}: MessageListProps) {
  const hasMessages = messages.length > 0;

  return (
    <div className="chat-scroll flex-1 space-y-4 overflow-y-auto px-4 py-6">
      {!hasMessages && (
        <div className="flex h-full flex-col items-center justify-center gap-2 text-center">
          <div className="text-3xl font-bold text-slate-300">?</div>
          <p className="text-sm font-medium text-slate-500">{emptyTitle}</p>
          <p className="max-w-sm text-xs text-slate-400">{emptyBody}</p>
        </div>
      )}
      {messages.map((turn, index) => (
        <MessageBubble key={`${turn.timestamp}-${index}`} turn={turn} />
      ))}
      {loading && <LoadingIndicator />}
    </div>
  );
}
