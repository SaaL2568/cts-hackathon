"use client";

export default function LoadingIndicator() {
  return (
    <div className="flex justify-start">
      <div className="flex items-center gap-1.5 rounded-2xl rounded-tl-sm border border-slate-200 bg-white px-4 py-3 shadow-sm">
        {[0, 1, 2].map((dot) => (
          <span
            key={dot}
            className="h-2 w-2 animate-bounce rounded-full bg-brand"
            style={{ animationDelay: `${dot * 0.15}s` }}
          />
        ))}
      </div>
    </div>
  );
}
