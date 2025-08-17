import './globals.css';
import type { Metadata } from 'next';
import React from 'react';
import Link from 'next/link';

export const metadata: Metadata = {
  title: 'Meeting Notes Summarizer',
  description: 'Turn transcripts into actionable summaries and share via email',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header className="border-b bg-background/70 backdrop-blur supports-[backdrop-filter]:bg-background/60">
          <div className="container flex h-14 items-center justify-between">
            <Link href="/" className="flex items-center gap-2 font-semibold">
              <span className="text-base text-xl font-bold text-gradient">MemoAI</span>
            </Link>
            <nav className="flex items-center gap-4 text-sm">
              <Link href="/" className="hover:underline">Home</Link>
              <Link href="/history" className="hover:underline">History</Link>
            </nav>
          </div>
        </header>
        <main className="container py-8">{children}</main>
      </body>
    </html>
  );
}