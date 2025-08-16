"use client";
import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { History as HistoryIcon, FileText, ExternalLink, AlertCircle, ArrowLeft } from "lucide-react";

export default function HistoryPage() {
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const list = await api.listMeetings();
        setItems(list);
      } catch (e: any) {
        setError(e?.message || 'Failed to load');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <div className="min-h-screen bg-muted/30 py-8">
      <div className="container mx-auto px-4 max-w-5xl">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold mb-2">
            Transcript <span className="text-gradient">History</span>
          </h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Browse previously generated meeting summaries
          </p>
        </div>

        <Card className="card-gradient hover-lift">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <HistoryIcon className="w-6 h-6 text-primary" />
                <CardTitle className="text-2xl">Saved Summaries</CardTitle>
              </div>
              <Badge variant="secondary" className="accent-gradient text-white">{items.length} items</Badge>
            </div>
            <CardDescription className="text-base">Open a summary to view or edit it</CardDescription>
          </CardHeader>
          <CardContent>
            {loading && (
              <div className="p-6 text-center text-muted-foreground">Loading…</div>
            )}

            {error && (
              <div className="flex items-center gap-2 p-3 mb-4 rounded-lg bg-destructive/10 border border-destructive/20">
                <AlertCircle className="w-4 h-4 text-destructive" />
                <p className="text-sm text-destructive">{error}</p>
              </div>
            )}

            {!loading && !error && items.length === 0 && (
              <div className="p-6 text-center">
                <p className="text-muted-foreground">No meetings yet. Generate one from the Home page.</p>
                <div className="mt-4">
                  <Link href="/">
                    <Button variant="outline" className="h-11">
                      <ArrowLeft className="w-4 h-4 mr-2" />
                      Back to Home
                    </Button>
                  </Link>
                </div>
              </div>
            )}

            {items.length > 0 && (
              <ul className="divide-y divide-border">
                {items.map((m) => (
                  <li key={m._id} className="py-4 flex items-center justify-between">
                    <div className="flex items-start gap-3">
                      <div className="mt-1">
                        <FileText className="w-5 h-5 text-muted-foreground" />
                      </div>
                      <div>
                        <div className="font-medium text-white/90 line-clamp-1">{m.title || 'Untitled Meeting'}</div>
                        <div className="text-sm text-muted-foreground">{new Date(m.createdAt).toLocaleString()}</div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Link href={`/meetings/${m._id}`}>
                        <Button variant="outline" size="sm">
                          <ExternalLink className="w-4 h-4 mr-2" />
                          Open
                        </Button>
                      </Link>
                    </div>
                  </li>
                ))}
              </ul>
            )}

            <Separator className="my-6" />

            <div className="flex justify-between">
              <Link href="/">
                <Button variant="outline" className="h-11">
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Back to Home
                </Button>
              </Link>
              <Link href="/">
                <Button className="h-11">
                  Generate New Summary
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
