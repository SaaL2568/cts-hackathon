"use client";

import { useRef, useState } from "react";
import { toast } from "sonner";

import { useDocumentUpload } from "@/hooks/useDocumentUpload";

interface DocumentUploadProps {
  onUploaded?: (docName: string) => void;
}

export default function DocumentUpload({ onUploaded }: DocumentUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const { uploading, result, error, upload, reset } = useDocumentUpload();

  const handleFile = async (file: File | undefined | null) => {
    if (!file) return;
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      toast.error("Only PDF files are accepted.");
      return;
    }
    try {
      const response = await upload(file);
      toast.success(`Indexed "${response.docName}" (${response.chunksIndexed} chunks).`);
      reset();
      onUploaded?.(response.docName);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Upload failed.";
      toast.error(message);
    }
  };

  const handleDragOver = (event: React.DragEvent) => {
    event.preventDefault();
    setDragging(true);
  };

  const handleDragLeave = (event: React.DragEvent) => {
    event.preventDefault();
    setDragging(false);
  };

  const handleDrop = (event: React.DragEvent) => {
    event.preventDefault();
    setDragging(false);
    void handleFile(event.dataTransfer.files?.[0]);
  };

  return (
    <div
      className={`rounded-xl border-2 border-dashed p-4 transition-colors ${
        dragging
          ? "border-brand bg-blue-50"
          : "border-slate-300 bg-white hover:border-brand"
      }`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".pdf"
        className="hidden"
        onChange={(event) => void handleFile(event.target.files?.[0])}
      />
      <button
        type="button"
        disabled={uploading}
        onClick={() => inputRef.current?.click()}
        className="w-full text-left text-sm font-medium text-slate-700"
      >
        {uploading ? (
          <span className="text-brand">Uploading and indexing...</span>
        ) : (
          <span>
            <span className="font-semibold text-brand">Upload a PDF</span> or drop it
            here
          </span>
        )}
      </button>
      {error && <p className="mt-2 text-xs text-red-600">{error}</p>}
      {result && (
        <p className="mt-2 text-xs text-emerald-700">
          Indexed {result.chunksIndexed} chunks across {result.pagesProcessed} pages.
        </p>
      )}
    </div>
  );
}
