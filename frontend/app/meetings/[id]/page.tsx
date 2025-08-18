"use client";
import React, { useEffect, useState } from 'react';
import { api } from '../../../lib/api';
import { useParams, useRouter } from 'next/navigation';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Sparkles, Mail, Save, Pencil, X } from "lucide-react";

export default function MeetingDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params?.id as string;

  const [meeting, setMeeting] = useState<any | null>(null);
  const [recipients, setRecipients] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    (async () => {
      try {
        const m = await api.getMeeting(id);
        setMeeting(m);
      } catch (e: any) {
        setError(e?.message || 'Failed to load');
      } finally {
        setLoading(false);
      }
    })();
  }, [id]);

  async function handleSaveEdited() {
    if (!meeting?._id) return;
    try {
      const updated = await api.updateMeeting(meeting._id, {
        title: meeting.title,
        instructions: meeting.instructions,
        summary: meeting.summary,
      });
      setMeeting(updated);
      setNotice('Saved changes.');
      setIsEditing(false);
    } catch (e: any) {
      setError(e?.message || 'Failed to save');
    }
  }

  async function handleSendEmail() {
    if (!meeting?._id) return;
    const to = recipients.split(',').map(s => s.trim()).filter(Boolean);
    if (!to.length) {
      setError('Please enter at least one recipient email');
      return;
    }
    try {
      setLoading(true);
      setError(null);
      await api.sendEmail(meeting._id, to, meeting.title || 'Meeting Summary', meeting.summary || '');
      setNotice('Email sent successfully.');
    } catch (e: any) {
      setError(e?.message || 'Failed to send email');
    } finally {
      setLoading(false);
    }
  }

  if (loading) return <p className="muted">Loading…</p>;
  if (error) return <p className="text-red-400">{error}</p>;
  if (!meeting) return <p className="muted">Not found</p>;

  return (
    <div className="grid gap-6">
      <section className="card p-5 md:p-6 hover-lift space-y-3">
        <div className="flex items-center justify-between">
          <button className="btn-ghost text-sm px-2 py-1 rounded-md" onClick={() => router.back()}>&larr; Back</button>
          <div className="flex items-center gap-2">
            {!isEditing ? (
              <button className="btn btn-primary" onClick={() => setIsEditing(true)}>
                <Pencil className="w-4 h-4 mr-2" /> Edit
              </button>
            ) : (
              <div className="flex gap-2">
                <button className="btn btn-primary" onClick={handleSaveEdited}>
                  <Save className="w-4 h-4 mr-2" /> Save
                </button>
                <button className="btn btn-ghost" onClick={() => setIsEditing(false)}>
                  <X className="w-4 h-4 mr-2" /> Cancel
                </button>
              </div>
            )}
          </div>
        </div>

        
        <div className="flex items-center gap-2 mb-2 mt-1">
          <Sparkles className="w-6 h-6 text-accent" />
          <h2 className="text-3xl md:text-4xl font-extrabold leading-tight">Meeting <span className="text-gradient">Summary</span></h2>
        </div>
        

        {/* View / Edit Toggle */}
        {isEditing ? (
          <>
            <input
              className="input mb-3"
              value={meeting.title || ''}
              onChange={e => setMeeting({ ...meeting, title: e.target.value })}
              placeholder="Title"
            />
            <label className="label">Instructions</label>
            <input
              className="input mb-3"
              value={meeting.instructions || ''}
              onChange={e => setMeeting({ ...meeting, instructions: e.target.value })}
              placeholder="Instructions"
            />
            <label className="label">Summary</label>
            <textarea
              className="textarea h-80"
              value={meeting.summary || ''}
              onChange={e => setMeeting({ ...meeting, summary: e.target.value })}
            />
          </>
        ) : (
          <>
            {/* Clean, styled view */}
            <h3 className="text-lg md:text-xl font-semibold leading-tight mb-1 text-white/90">{meeting.title || 'Untitled Meeting'}</h3>
            {meeting.instructions ? (
              <p className="text-white/80 font-medium leading-snug mb-3">{meeting.instructions}</p>
            ) : null}
            <div className="p-5 md:p-6 rounded-2xl border border-white/10 bg-white/5">
              <div className="max-w-none markdown-body">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {meeting.summary || ''}
                </ReactMarkdown>
              </div>
            </div>
          </>
        )}

        <div className="my-2 border-t border-white/10" />

        <div className="flex gap-3 mt-4 flex-wrap items-center">
          <input
            className="input flex-1"
            placeholder="recipient1@example.com, recipient2@example.com"
            value={recipients}
            onChange={e => setRecipients(e.target.value)}
          />
          <button className="btn btn-secondary" onClick={handleSendEmail}>
            <Mail className="w-4 h-4 mr-2" /> Send Email
          </button>
          {notice ? <span className="text-green-400 text-sm">{notice}</span> : null}
          {isEditing ? (
            <>
              <button className="btn btn-primary" onClick={handleSaveEdited}>
                <Save className="w-4 h-4 mr-2" /> Save
              </button>
              <button className="btn btn-ghost" onClick={() => setIsEditing(false)}>
                <X className="w-4 h-4 mr-2" /> Cancel
              </button>
            </>
          ) : (
            <button className="btn btn-primary" onClick={() => setIsEditing(true)}>
              <Pencil className="w-4 h-4 mr-2" /> Edit
            </button>
          )}
        </div>
      </section>
    </div>
  );
}
