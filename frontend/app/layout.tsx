import './globals.css';
import type { Metadata } from 'next';
import React from 'react';

export const metadata: Metadata = {
  title: 'Meeting Notes Summarizer',
  description: 'Turn transcripts into actionable summaries and share via email',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <main className="container py-8">{children}</main>
      </body>
    </html>
  );
}