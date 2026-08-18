"use client";

import { useCallback, useEffect, useState } from "react";

import { queryChat } from "@/lib/api";
import type { ChatTurn } from "@/lib/types";

const STORAGE_PREFIX = "cts-chat-messages-";

function readMessages(sessionId: string): ChatTurn[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(`${STORAGE_PREFIX}${sessionId}`);
    return raw ? (JSON.parse(raw) as ChatTurn[]) : [];
  } catch {
    return [];
  }
}

export function useChat(sessionId: string | null) {
  const [messages, setMessages] = useState<ChatTurn[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setMessages(sessionId ? readMessages(sessionId) : []);
    setError(null);
  }, [sessionId]);

  const persist = useCallback(
    (next: ChatTurn[]) => {
      if (!sessionId || typeof window === "undefined") return;
      window.localStorage.setItem(`${STORAGE_PREFIX}${sessionId}`, JSON.stringify(next));
    },
    [sessionId],
  );

  const sendMessage = useCallback(
    async (question: string) => {
      if (!sessionId || loading) return;
      const trimmed = question.trim();
      if (!trimmed) return;

      setError(null);
      const userTurn: ChatTurn = {
        role: "user",
        content: trimmed,
        citations: [],
        refused: false,
        timestamp: new Date().toISOString(),
      };
      const withUser = [...messages, userTurn];
      setMessages(withUser);
      setLoading(true);

      try {
        const result = await queryChat(sessionId, trimmed);
        const assistantTurn: ChatTurn = {
          role: "assistant",
          content: result.answer,
          citations: result.citations,
          refused: result.refused,
          timestamp: new Date().toISOString(),
        };
        const next = [...withUser, assistantTurn];
        setMessages(next);
        persist(next);
      } catch (err) {
        const message = err instanceof Error ? err.message : "Failed to get an answer.";
        setError(message);
        persist(withUser);
      } finally {
        setLoading(false);
      }
    },
    [sessionId, loading, messages, persist],
  );

  const clearMessages = useCallback(() => {
    setMessages([]);
    if (sessionId && typeof window !== "undefined") {
      window.localStorage.removeItem(`${STORAGE_PREFIX}${sessionId}`);
    }
  }, [sessionId]);

  return { messages, loading, error, sendMessage, clearMessages };
}
