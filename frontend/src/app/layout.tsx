import type { Metadata } from "next";
import { Toaster } from "sonner";

import "./globals.css";

export const metadata: Metadata = {
  title: "Drug Info Q&A Chatbot",
  description:
    "Grounded Q&A over FDA drug prescribing information with citations.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="bg-slate-50 text-slate-900 antialiased">
        {children}
        <Toaster position="top-right" richColors />
      </body>
    </html>
  );
}
