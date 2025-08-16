const BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000';

async function handle(res: Response) {
  if (!res.ok) {
    const msg = await res.text().catch(() => 'Error');
    throw new Error(msg || res.statusText);
  }
  const ct = res.headers.get('content-type') || '';
  if (ct.includes('application/json')) return res.json();
  return res.text();
}

export const api = {
  async createSummary({ title, text, instructions, file }: { title?: string; text?: string; instructions?: string; file?: File | null }) {
    const form = new FormData();
    if (title) form.set('title', title);
    if (instructions) form.set('instructions', instructions);
    if (file) form.set('file', file);
    if (text) form.set('text', text);

    const res = await fetch(`${BASE}/api/meetings/summarize`, {
      method: 'POST',
      body: form,
    });
    return handle(res);
  },

  async listMeetings() {
    const res = await fetch(`${BASE}/api/meetings`, { cache: 'no-store' });
    return handle(res);
  },

  async getMeeting(id: string) {
    const res = await fetch(`${BASE}/api/meetings/${id}`, { cache: 'no-store' });
    return handle(res);
  },

  async updateMeeting(id: string, body: { title?: string; instructions?: string; summary?: string }) {
    const res = await fetch(`${BASE}/api/meetings/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    return handle(res);
  },

  async sendEmail(id: string, to: string[], subject?: string) {
    const res = await fetch(`${BASE}/api/meetings/${id}/email`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ to, subject }),
    });
    return handle(res);
  },
};
