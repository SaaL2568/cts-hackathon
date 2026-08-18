"use client";

import { useCallback, useState } from "react";

import { uploadDocument } from "@/lib/api";
import type { UploadDocumentResponse } from "@/lib/types";

export function useDocumentUpload() {
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<UploadDocumentResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const upload = useCallback(async (file: File): Promise<UploadDocumentResponse> => {
    setUploading(true);
    setError(null);
    setResult(null);
    try {
      const response = await uploadDocument(file, file.name.replace(/\.pdf$/i, ""));
      setResult(response);
      return response;
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Upload failed. Is the backend running?";
      setError(message);
      throw err;
    } finally {
      setUploading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setResult(null);
    setError(null);
  }, []);

  return { uploading, result, error, upload, reset };
}
