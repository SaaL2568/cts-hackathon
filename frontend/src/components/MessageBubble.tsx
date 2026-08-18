"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import type { ChatTurn } from "@/lib/types";
import CitationCard from "./CitationCard";

export default function MessageBubble({ turn }: { turn: ChatTurn }) {
  const isUser = turn.role === "user";

  if (isUser) {
    return (
      <div className="flex justify-end">
        <div className="max-w-[75%] rounded-2xl rounded-tr-sm bg-brand px-4 py-2.5 text-sm text-white">
          {turn.content}
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-start">
      <div className="max-w-[85%] space-y-3">
        {turn.refused && (
          <div className="flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2">
            <span className="mt-0.5 text-amber-500" aria-hidden>
              !
            </span>
            <p className="text-xs font-medium text-amber-800">
              The assistant could not answer from the available information and
              declined to guess.
            </p>
          </div>
        )}
        <div className="rounded-2xl rounded-tl-sm border border-slate-200 bg-white px-4 py-2.5 text-sm leading-relaxed text-slate-800 shadow-sm">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
              ul: ({ children }) => (
                <ul className="mb-2 list-disc space-y-1 pl-5 last:mb-0">{children}</ul>
              ),
              ol: ({ children }) => (
                <ol className="mb-2 list-decimal space-y-1 pl-5 last:mb-0">{children}</ol>
              ),
              strong: ({ children }) => (
                <strong className="font-semibold">{children}</strong>
              ),
              a: (props) => (
                <a
                  {...props}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-brand underline"
                />
              ),
            }}
          >
            {turn.content}
          </ReactMarkdown>
        </div>
        {turn.citations.length > 0 && (
          <div className="space-y-2">
            {turn.citations.map((citation, index) => (
              <CitationCard key={`${citation.docName}-${citation.pageNum}-${index}`} citation={citation} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
