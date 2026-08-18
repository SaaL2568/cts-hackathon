"use client";

import { useEffect, useRef, useState } from "react";
import { toast } from "sonner";

import { useChat } from "@/hooks/useChat";
import { useSessions } from "@/hooks/useSessions";
import MessageList from "./MessageList";
import SessionSidebar from "./SessionSidebar";

export default function ChatInterface() {
  const {
    sessions,
    currentSessionId,
    ready,
    creating,
    addSession,
    removeSession,
    selectSession,
  } = useSessions();

  const { messages, loading, error, sendMessage, clearMessages } = useChat(
    currentSessionId,
  );

  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!ready && sessions.length === 0) {
      void addSession();
    }
  }, [ready, sessions.length, addSession]);

  useEffect(() => {
    if (error) toast.error(error);
  }, [error]);

  useEffect(() => {
    const element = scrollRef.current;
    if (element) element.scrollTop = element.scrollHeight;
  }, [messages, loading]);

  const handleSend = () => {
    if (loading || !input.trim()) return;
    void sendMessage(input);
    setInput("");
  };

  return (
    <div className="flex h-screen">
      <SessionSidebar
        sessions={sessions}
        currentSessionId={currentSessionId}
        creating={creating}
        onAddSession={addSession}
        onSelectSession={selectSession}
        onRemoveSession={removeSession}
      />

      <main className="flex flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-slate-200 bg-white px-6 py-3">
          <div>
            <h2 className="text-sm font-semibold text-slate-800">Chat</h2>
            <p className="text-xs text-slate-400">
              Every answer is grounded in the source document with page citations.
            </p>
          </div>
          {messages.length > 0 && (
            <button
              type="button"
              onClick={clearMessages}
              className="text-xs text-slate-400 hover:text-slate-600"
            >
              Clear history
            </button>
          )}
        </header>

        <div ref={scrollRef} className="flex flex-1 overflow-hidden">
          <MessageList
            messages={messages}
            loading={loading}
            emptyTitle={
              currentSessionId
                ? "Ask about an ingested drug label"
                : "Create a session to start chatting"
            }
            emptyBody="Drug label PDFs are automatically loaded on startup. Ask any question about a loaded drug and get answers with page-level citations."
          />
        </div>

        <footer className="border-t border-slate-200 bg-white px-6 py-4">
          <div className="flex items-end gap-3">
            <textarea
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  handleSend();
                }
              }}
              rows={1}
              placeholder="Ask a question about the drug label..."
              disabled={loading}
              className="max-h-32 flex-1 resize-none rounded-xl border border-slate-300 px-4 py-2.5 text-sm outline-none transition-colors focus:border-brand disabled:bg-slate-50"
            />
            <button
              type="button"
              onClick={handleSend}
              disabled={loading || !input.trim()}
              className="rounded-xl bg-brand px-5 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-brand-dark disabled:opacity-50"
            >
              {loading ? "Thinking..." : "Send"}
            </button>
          </div>
          <p className="mt-2 text-right text-[10px] text-slate-400">
            Do not rely on answers for medical decisions. Citations reference the
            source label page.
          </p>
        </footer>
      </main>
    </div>
  );
}
