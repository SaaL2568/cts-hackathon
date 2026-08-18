"use client";

import { useCallback, useEffect, useState } from "react";

import { createSession } from "@/lib/api";

const STORAGE_KEY = "cts-chat-sessions";

export interface SessionMeta {
  id: string;
  createdAt: string;
}

function readSessions(): SessionMeta[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as SessionMeta[]) : [];
  } catch {
    return [];
  }
}

export function useSessions() {
  const [sessions, setSessions] = useState<SessionMeta[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [ready, setReady] = useState(false);
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    const stored = readSessions();
    setSessions(stored);
    setCurrentSessionId(stored[0]?.id ?? null);
    setReady(true);
  }, []);

  const persist = useCallback((next: SessionMeta[]) => {
    setSessions(next);
    if (typeof window !== "undefined") {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
    }
  }, []);

  const addSession = useCallback(async (): Promise<string> => {
    setCreating(true);
    try {
      const { sessionId } = await createSession();
      const meta: SessionMeta = {
        id: sessionId,
        createdAt: new Date().toISOString(),
      };
      const next = [meta, ...sessions];
      persist(next);
      setCurrentSessionId(sessionId);
      return sessionId;
    } finally {
      setCreating(false);
    }
  }, [sessions, persist]);

  const removeSession = useCallback(
    (sessionId: string) => {
      const next = sessions.filter((session) => session.id !== sessionId);
      persist(next);
      if (typeof window !== "undefined") {
        window.localStorage.removeItem(`cts-chat-messages-${sessionId}`);
      }
      setCurrentSessionId((current) =>
        current === sessionId ? (next[0]?.id ?? null) : current,
      );
    },
    [sessions, persist],
  );

  const selectSession = useCallback((sessionId: string) => {
    setCurrentSessionId(sessionId);
  }, []);

  return {
    sessions,
    currentSessionId,
    ready,
    creating,
    addSession,
    removeSession,
    selectSession,
  };
}
