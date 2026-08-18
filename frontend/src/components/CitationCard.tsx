"use client";

import { useState } from "react";

import type { Citation } from "@/lib/types";

export default function CitationCard({ citation }: { citation: Citation }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="rounded-lg border border-blue-200 bg-blue-50/60 px-3 py-2">
      <button
        type="button"
        onClick={() => setExpanded((value) => !value)}
        className="flex w-full items-center gap-2 text-left"
      >
        <span className="rounded bg-brand px-1.5 py-0.5 text-[10px] font-semibold text-white">
          SOURCE
        </span>
        <span className="text-xs font-medium text-slate-700">
          {citation.docName}, page {citation.pageNum}
        </span>
        <span className="ml-auto text-[10px] text-slate-400">
          {expanded ? "hide" : "snippet"}
        </span>
      </button>
      {expanded && (
        <p className="mt-1.5 line-clamp-4 text-xs leading-relaxed text-slate-600">
          {citation.snippet}
        </p>
      )}
    </div>
  );
}
