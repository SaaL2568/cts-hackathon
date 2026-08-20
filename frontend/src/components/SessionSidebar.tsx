"use client";

import { useCallback, useEffect, useState } from "react";

import { listDocuments } from "@/lib/api";
import type { SessionMeta } from "@/hooks/useSessions";

interface SessionSidebarProps {
  sessions: SessionMeta[];
  currentSessionId: string | null;
  creating: boolean;
  onAddSession: () => Promise<string>;
  onSelectSession: (sessionId: string) => void;
  onRemoveSession: (sessionId: string) => void;
}

export default function SessionSidebar({
  sessions,
  currentSessionId,
  creating,
  onAddSession,
  onSelectSession,
  onRemoveSession,
}: SessionSidebarProps) {
  const [documents, setDocuments] = useState<string[]>([]);
  const [loadingDocs, setLoadingDocs] = useState(true);

  const fetchDocuments = useCallback(async () => {
    try {
      setLoadingDocs(true);
      const response = await listDocuments();
      setDocuments(response.documents);
    } catch {
      // Silently handle — backend may not be ready yet
    } finally {
      setLoadingDocs(false);
    }
  }, []);

  useEffect(() => {
    void fetchDocuments();
  }, [fetchDocuments]);

  return (
    <aside className="flex h-full w-72 flex-col border-r border-slate-200 bg-white">
      <div className="flex items-center justify-between px-4 py-4">
        <h1 className="text-sm font-bold text-slate-800">Drug Info Q&A</h1>
        <button
          type="button"
          disabled={creating}
          onClick={() => void onAddSession()}
          className="rounded-lg bg-brand px-2.5 py-1.5 text-xs font-semibold text-white transition-colors hover:bg-brand-dark disabled:opacity-50"
        >
          {creating ? "Creating..." : "New chat"}
        </button>
      </div>

      <div className="chat-scroll flex-1 space-y-1 overflow-y-auto px-2">
        {sessions.length === 0 && (
          <p className="px-2 py-4 text-center text-xs text-slate-400">
            No sessions yet. Start a new chat.
          </p>
        )}
        {sessions.map((session) => {
          const isActive = session.id === currentSessionId;
          return (
            <div
              key={session.id}
              className={`group flex items-center rounded-lg px-3 py-2 transition-colors ${
                isActive ? "bg-blue-50" : "hover:bg-slate-50"
              }`}
            >
              <button
                type="button"
                onClick={() => onSelectSession(session.id)}
                className="min-w-0 flex-1 truncate text-left text-sm"
              >
                <span className={isActive ? "font-semibold text-brand" : "text-slate-700"}>
                  {formatSessionLabel(session.createdAt, session.id)}
                </span>
              </button>
              <button
                type="button"
                aria-label="Delete session"
                onClick={() => onRemoveSession(session.id)}
                className="ml-2 hidden text-xs text-slate-400 hover:text-red-600 group-hover:block"
              >
                x
              </button>
            </div>
          );
        })}
      </div>

      {/* Ingested Documents List - Moved to bottom and made collapsible */}
      <div className="mt-auto px-4 pb-3 border-t border-slate-200 pt-3">
        <details className="rounded-xl border border-slate-200 bg-slate-50 group">
          <summary className="flex cursor-pointer items-center justify-between p-3 outline-none select-none">
            <h3 className="text-xs font-semibold text-slate-600 uppercase tracking-wider">
              Ingested Documents
            </h3>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={(e) => {
                  e.preventDefault();
                  void fetchDocuments();
                }}
                className="text-[10px] text-slate-400 hover:text-brand transition-colors"
                title="Refresh list"
              >
                ↻
              </button>
              <span className="text-slate-400 transition-transform group-open:rotate-180">▼</span>
            </div>
          </summary>
          <div className="p-3 pt-0">
            {loadingDocs ? (
              <p className="text-[11px] text-slate-400">Loading...</p>
            ) : documents.length === 0 ? (
              <p className="text-[11px] text-slate-400">No documents ingested yet.</p>
            ) : (
              <div className="flex max-h-40 flex-wrap gap-1.5 overflow-y-auto">
                {documents.map((name) => (
                  <span
                    key={name}
                    className="inline-block rounded-md bg-blue-100 px-2 py-0.5 text-[11px] font-medium text-blue-700"
                    title={name}
                  >
                    {name}
                  </span>
                ))}
              </div>
            )}
          </div>
        </details>
      </div>

      <div className="border-t border-slate-200 px-4 py-3 text-[10px] leading-relaxed text-slate-400">
        Answers are grounded in FDA prescribing information PDFs loaded on
        startup and include page citations.
      </div>
    </aside>
  );
}

function formatSessionLabel(createdAt: string, sessionId: string): string {
  const date = new Date(createdAt);
  if (Number.isNaN(date.getTime())) return `Session ${sessionId.slice(0, 8)}`;
  return date.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

