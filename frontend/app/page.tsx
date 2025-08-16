"use client";
import React, { useMemo, useRef, useState, useEffect } from 'react';
import Link from 'next/link';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { FileText, Upload, Sparkles, Save, Mail, History, AlertCircle } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { api } from "@/lib/api";

// Using real backend API from '@/lib/api'

export default function ImprovedSummaryInterface() {
  const [title, setTitle] = useState('');
  const [text, setText] = useState('');
  const [instructions, setInstructions] = useState('Executive summary in bullet points');
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [meeting, setMeeting] = useState<any | null>(null);
  const [recipients, setRecipients] = useState('');
  const { toast } = useToast();
  const summaryRef = useRef<HTMLDivElement | null>(null);

  // Auto-scroll to summary section when a meeting is set
  useEffect(() => {
    if (meeting && summaryRef.current) {
      summaryRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }, [meeting]);

  const canGenerate = useMemo(() => (text && text.trim().length > 0) || file, [text, file]);

  async function handleGenerate() {
    setLoading(true);
    setError(null);
    try {
      const data = await api.createSummary({ title, text, instructions, file });
      setMeeting(data);
    } catch (e: any) {
      const errorMessage = e?.message || 'Failed to generate summary';
      setError(errorMessage);
      toast({
        title: "Generation failed",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  }

  async function handleSaveEdited() {
    if (!meeting?._id) return;
    try {
      const updated = await api.updateMeeting(meeting._id, {
        title: meeting.title,
        instructions: meeting.instructions,
        summary: meeting.summary,
      });
      setMeeting(updated);
      toast({
        title: "Summary saved",
        description: "Your changes have been saved successfully.",
      });
    } catch (e: any) {
      const errorMessage = e?.message || 'Failed to save';
      setError(errorMessage);
      toast({
        title: "Save failed",
        description: errorMessage,
        variant: "destructive",
      });
    }
  }

  async function handleSendEmail() {
    if (!meeting?._id) return;
    const to = recipients.split(',').map(s => s.trim()).filter(Boolean);
    if (!to.length) {
      setError('Please enter at least one recipient email');
      toast({
        title: "Missing recipients",
        description: "Please enter at least one recipient email address.",
        variant: "destructive",
      });
      return;
    }
    try {
      setLoading(true);
      setError(null);
      await api.sendEmail(meeting._id, to, meeting.title || 'Meeting Summary');
      toast({
        title: "Email sent successfully",
        description: `Summary sent to ${to.length} recipient${to.length > 1 ? 's' : ''}.`,
      });
      setRecipients('');
    } catch (e: any) {
      const errorMessage = e?.message || 'Failed to send email';
      setError(errorMessage);
      toast({
        title: "Email failed",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0] || null;
    setFile(selectedFile);
    if (selectedFile) {
      toast({
        title: "File selected",
        description: `Selected: ${selectedFile.name}`,
      });
    }
  };

  return (
    <div className="min-h-screen bg-muted/30 py-8">
      <div className="container mx-auto px-4 max-w-6xl">
        {/* Header Section */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold mb-2">
            AI Meeting <span className="text-gradient">Summarizer</span>
          </h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Transform lengthy meeting transcripts into actionable summaries with AI assistance
          </p>
        </div>

        <div className="grid gap-8">
          {/* Input Section */}
          <Card className="card-gradient hover-lift">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <FileText className="w-6 h-6 text-primary" />
                  <CardTitle className="text-2xl">Create Summary</CardTitle>
                </div>
                <Badge variant="secondary" className="accent-gradient text-white">
                  <Sparkles className="w-3 h-3 mr-1" />
                  AI-Powered
                </Badge>
              </div>
              <CardDescription className="text-base">
                Upload a transcript or paste meeting text to generate an intelligent summary
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Title and Instructions Row */}
              <div className="grid md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="title" className="text-sm font-medium">Meeting Title (Optional)</Label>
                  <Input
                    id="title"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="e.g., Sprint Review 2025-08-16"
                    className="h-11"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="instructions" className="text-sm font-medium">Custom Instructions</Label>
                  <Input
                    id="instructions"
                    value={instructions}
                    onChange={(e) => setInstructions(e.target.value)}
                    placeholder="e.g., Focus on action items and deadlines"
                    className="h-11"
                  />
                </div>
              </div>

              <Separator />

              {/* Transcript Input */}
              <div className="space-y-3">
                <Label htmlFor="transcript" className="text-sm font-medium">Meeting Transcript</Label>
                <Textarea
                  id="transcript"
                  placeholder="Paste your meeting transcript here..."
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  className="min-h-[200px] resize-none"
                />
              </div>

              {/* File Upload */}
              <div className="space-y-3">
                <Label className="text-sm font-medium">Or Upload File</Label>
                <div className="relative">
                  <div className="border-2 border-dashed border-border rounded-lg p-6 text-center hover:bg-muted/50 transition-colors">
                    <Upload className="w-8 h-8 text-muted-foreground mx-auto mb-2" />
                    <div className="space-y-1">
                      <p className="text-sm text-muted-foreground">
                        {file ? file.name : "Click to upload or drag and drop"}
                      </p>
                      <Badge variant="outline" className="text-xs">
                        Supports .txt files
                      </Badge>
                    </div>
                    <input
                      type="file"
                      accept="text/plain"
                      onChange={handleFileChange}
                      className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                    />
                  </div>
                </div>
              </div>

              {/* Error Display */}
              {error && (
                <div className="flex items-center gap-2 p-3 rounded-lg bg-destructive/10 border border-destructive/20">
                  <AlertCircle className="w-4 h-4 text-destructive" />
                  <p className="text-sm text-destructive">{error}</p>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex flex-col sm:flex-row gap-3 pt-2">
                <Button
                  onClick={handleGenerate}
                  disabled={!canGenerate || loading}
                  className="btn-primary-gradient flex-1 h-11"
                  size="lg"
                >
                  {loading ? (
                    <>
                      <Sparkles className="w-4 h-4 mr-2 animate-spin" />
                      Generating Summary...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4 mr-2" />
                      Generate AI Summary
                    </>
                  )}
                </Button>
                <Link href="/history">
                  <Button variant="outline" size="lg" className="h-11">
                    <History className="w-4 h-4 mr-2" />
                    View History
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>

          {/* Output Section */}
          {meeting && (
            <div ref={summaryRef}>
              <Card className="card-gradient hover-lift">
                <CardHeader>
                  <div className="flex items-center gap-2">
                    <Sparkles className="w-6 h-6 text-accent" />
                    <CardTitle className="text-2xl">Generated Summary</CardTitle>
                  </div>
                  <CardDescription className="text-base">
                    Review and edit your AI-generated summary before sharing
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Editable Title */}
                  <div className="space-y-2">
                    <Label htmlFor="summary-title" className="text-sm font-medium">Summary Title</Label>
                    <Input
                      id="summary-title"
                      value={meeting.title || ''}
                      onChange={(e) => setMeeting({ ...meeting, title: e.target.value })}
                      placeholder="Enter a concise summary title"
                      className="h-11 font-medium"
                    />
                  </div>

                  {/* Editable Summary */}
                  <div className="space-y-2">
                    <Label htmlFor="summary-content" className="text-sm font-medium">Summary Content</Label>
                    <Textarea
                      id="summary-content"
                      value={meeting.summary || ''}
                      onChange={(e) => setMeeting({ ...meeting, summary: e.target.value })}
                      className="min-h-[300px] font-mono text-sm leading-relaxed"
                    />
                  </div>

                  <Separator />

                  {/* Email Section */}
                <div className="space-y-3">
                  <Label htmlFor="recipients" className="text-sm font-medium">Email Recipients</Label>
                  <div className="flex flex-col sm:flex-row gap-3">
                    <Input
                      id="recipients"
                      placeholder="recipient1@example.com, recipient2@example.com"
                      value={recipients}
                      onChange={(e) => setRecipients(e.target.value)}
                      className="flex-1 h-11"
                    />
                    <div className="flex gap-2">
                      <Button 
                        onClick={handleSaveEdited}
                        variant="outline" 
                        size="lg"
                        className="h-11"
                      >
                        <Save className="w-4 h-4 mr-2" />
                        Save
                      </Button>
                      <Button 
                        onClick={handleSendEmail}
                        disabled={loading}
                        className="h-11"
                        size="lg"
                      >
                        <Mail className="w-4 h-4 mr-2" />
                        Send Email
                      </Button>
                    </div>
                  </div>
                </div>
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}