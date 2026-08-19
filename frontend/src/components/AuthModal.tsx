"use client";

import { useState } from "react";
import { getAuthToken, setAuthToken } from "@/lib/api";

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function AuthModal({ isOpen, onClose }: AuthModalProps) {
  const [token, setTokenState] = useState(getAuthToken());
  const [saved, setSaved] = useState(false);

  if (!isOpen) return null;

  const handleSave = () => {
    setAuthToken(token.trim());
    setSaved(true);
    setTimeout(() => {
      setSaved(false);
      onClose();
    }, 600);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
      <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl">
        <h3 className="text-lg font-semibold text-slate-800">API Authentication Token</h3>
        <p className="mt-1 text-xs text-slate-500">
          Enter the Bearer token required for API requests.
        </p>

        <div className="mt-4">
          <label className="block text-xs font-medium text-slate-700">Auth Secret / Token</label>
          <input
            type="password"
            value={token}
            onChange={(e) => setTokenState(e.target.value)}
            placeholder="e.g. dev-secret-key-change-me"
            className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-brand"
          />
        </div>

        <div className="mt-6 flex justify-end gap-3">
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg border border-slate-200 px-4 py-2 text-xs font-medium text-slate-600 hover:bg-slate-50"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleSave}
            className="rounded-lg bg-brand px-4 py-2 text-xs font-medium text-white hover:bg-brand-dark"
          >
            {saved ? "Saved!" : "Save Token"}
          </button>
        </div>
      </div>
    </div>
  );
}
