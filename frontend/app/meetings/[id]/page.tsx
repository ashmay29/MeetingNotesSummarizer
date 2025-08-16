"use client";
import React, { useEffect, useState } from 'react';
import { api } from '../../../lib/api';
import { useParams, useRouter } from 'next/navigation';

export default function MeetingDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params?.id as string;

  const [meeting, setMeeting] = useState<any | null>(null);
  const [recipients, setRecipients] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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
      alert('Saved');
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
      await api.sendEmail(meeting._id, to, meeting.title || 'Meeting Summary');
      alert('Email sent');
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
    <div className="grid gap-8">
      <section className="card p-6 md:p-8">
        <button className="btn-ghost text-sm px-2 py-1 rounded-md" onClick={() => router.back()}>&larr; Back</button>
        <h2 className="h2 mb-4 mt-3">Meeting Detail</h2>
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
        <div className="flex gap-3 mt-4 flex-wrap">
          <input
            className="input flex-1"
            placeholder="recipient1@example.com, recipient2@example.com"
            value={recipients}
            onChange={e => setRecipients(e.target.value)}
          />
          <button className="btn btn-secondary" onClick={handleSendEmail}>Send Email</button>
          <button className="btn btn-primary" onClick={handleSaveEdited}>Save</button>
        </div>
      </section>
    </div>
  );
}
