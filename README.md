# MeetingNotesSummarizer
AI-Powered Meeting Notes Summarizer & Sharer is a full-stack application that turns lengthy meeting transcripts into concise, actionable summaries. Users can upload transcripts or paste text, provide custom instructions (e.g., "Highlight only deadlines" or "Executive summary in bullet points"), edit the output, and email it to recipients. A history of transcripts/summaries is stored in MongoDB.

## Tech Stack
- Frontend: Next.js 14 (App Router) + TypeScript + Tailwind CSS
- Backend: Node.js + Express + TypeScript
- Database: MongoDB (Mongoose)
- Email: Nodemailer (SMTP)

## Color Theme (Beige/Cream/Brown)
- Cream: `cream-50/100/200/300`
- Beige: `beige-200/300/400`
- Brown: `brown-500/600/700`
Defined in `frontend/tailwind.config.ts` and used in `frontend/app/globals.css`.

## Folder Structure
```
backend/   # Express API, MongoDB models, summarizer and mailer services
  src/
    index.ts
    lib/db.ts
    models/Meeting.ts
    routes/meetings.ts
    services/{summarizer.ts, mailer.ts}
  .env.example
  package.json
  tsconfig.json

frontend/  # Next.js + Tailwind UI
  app/
    layout.tsx
    page.tsx
    history/page.tsx
    meetings/[id]/page.tsx
    globals.css
  lib/api.ts
  .env.example
  package.json
  tailwind.config.ts
  postcss.config.mjs
  tsconfig.json
```

## Prerequisites
- Node.js 18+
- MongoDB running locally (or a connection string)

## Setup & Run (Windows)
1) Backend
```
copy backend\.env.example backend\.env
cd backend
npm install
npm run dev
```
Backend runs on http://localhost:4000

2) Frontend
```
copy frontend\.env.example frontend\.env
cd frontend
npm install
npm run dev
```
Frontend runs on http://localhost:3000

3) MongoDB
- Default URI: `mongodb://127.0.0.1:27017/meeting-notes-summarizer` (defined in `backend/.env.example`)
- Update `MONGO_URI` in `backend/.env` if needed.

4) Email (optional for sending summaries)
- Configure SMTP in `backend/.env` (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `MAIL_FROM`).

## API Endpoints (backend)
- `GET /api/health` – health check
- `GET /api/meetings` – list recent meetings
- `GET /api/meetings/:id` – get a meeting
- `POST /api/meetings/summarize` – create + summarize
  - multipart/form-data: `text` (string) or `file` (text/plain), optional `title`, `instructions`
- `PUT /api/meetings/:id` – update `title`, `summary`, `instructions`
- `POST /api/meetings/:id/email` – body: `{ to: string[], subject?: string }`

## Notes on Summarization
- Local, cost-free summarizer in `backend/src/services/summarizer.ts` using sentence scoring and simple instruction-aware filters.
- Supports bullet point formatting when instructions include words like "bullet" or "list".

## Scripts
- Backend: `npm run dev` (ts-node-dev), `npm run build`, `npm start`
- Frontend: `npm run dev`, `npm run build`, `npm start`

## License
MIT
