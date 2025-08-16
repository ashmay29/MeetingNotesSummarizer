import re
import os
from typing import List, Optional
import google.generativeai as genai 

def sentence_split(text: str) -> List[str]:
    sentences = re.sub(r"\n+", " ", text)
    parts = re.split(r"(?<=[.!?])\s+", sentences)
    return [s.strip() for s in parts if s and s.strip()]


def score_sentences(sentences: List[str]) -> dict[str, float]:
    stop = set(
        "a,an,the,and,or,but,if,then,else,for,of,in,on,at,by,to,from,with,as,that,this,these,those,is,are,was,were,be,been,being,can,could,should,would,may,might,will,shall,do,does,did,have,has,had".split(",")
    )
    freq: dict[str, int] = {}
    for s in sentences:
        for w in re.findall(r"[a-z0-9'-]+", s.lower()):
            if w in stop:
                continue
            freq[w] = freq.get(w, 0) + 1
    scores: dict[str, float] = {}
    for s in sentences:
        score = 0
        words = re.findall(r"[a-z0-9'-]+", s.lower())
        for w in words:
            if w in stop:
                continue
            score += freq.get(w, 0)
        length = max(5, len(re.findall(r"\S+", s)))
        scores[s] = score / length
    return scores


def apply_instruction_filters(sentences: List[str], instructions: str | None) -> List[str]:
    """
    Filter sentences based on user instructions. If multiple categories are requested
    (e.g., actions AND deadlines), include sentences that match ANY requested category
    instead of requiring ALL. If no categories are detected, return the original list.

    Note: For more robust NLP (sentence splitting, tokenization, lemmatization, NER),
    consider integrating spaCy or NLTK. This function intentionally remains regex-based
    and dependency-light.
    """
    if not instructions:
        return sentences

    instr = instructions.lower()

    # Organized pattern definitions for maintainability
    patterns = {
        "deadlines": re.compile(r"deadline|due|by\s+\d{1,2}\/(\d{1,2}|\d{4})|eod|eow", re.I),
        "actions": re.compile(r"action|todo|follow[- ]?up|task|next step", re.I),
        "decisions": re.compile(r"decision|agreed|conclude|finalize", re.I),
        "risks": re.compile(r"risk|blocker|issue|concern", re.I),
        "owners": re.compile(r"owner|assign|responsible|who", re.I),
    }

    requested = {
        key: bool(p.search(instr)) for key, p in patterns.items()
    }

    # If no specific category requested, return sentences unchanged
    if not any(requested.values()):
        return sentences

    sentence_matchers = {
        "deadlines": re.compile(r"deadline|due|by\s+\w+\s*\d{1,2}|\b\d{1,2}\/\d{1,2}\b|eod|eow|tomorrow|next week", re.I),
        "actions": re.compile(r"\b(we|i|they)\s+(will|need to|must|should)|action|todo|follow[- ]?up|task|next step", re.I),
        "decisions": re.compile(r"decided|agreed|approved|concluded|finalized", re.I),
        "risks": re.compile(r"risk|blocker|issue|concern|problem", re.I),
        "owners": re.compile(r"@?\b[A-Z][a-z]+\b|assigned to|owner|responsible", re.I),
    }

    filtered: List[str] = []
    seen = set()
    for s in sentences:
        # Include sentence if it matches ANY requested category
        for key, want in requested.items():
            if not want:
                continue
            if sentence_matchers[key].search(s):
                if s not in seen:
                    filtered.append(s)
                    seen.add(s)
                break  # no need to test other categories once matched

    return filtered or sentences


def _clean_transcript(text: str) -> str:
    """
    Lightweight NLP-style cleaning suitable for long transcripts.
    - Remove timestamps like [03:45 PM], (00:12:34), 12:34, 03/12/2025 14:33
    - Collapse multiple spaces/newlines
    - Remove common filler words (um, uh) when standalone
    - Normalize bullets/dashes
    - Strip leading/trailing whitespace
    """
    t = text
    # Remove bracketed timestamps
    t = re.sub(r"\[(?:\d{1,2}:)?\d{1,2}:\d{2}\s*(?:AM|PM)?\]", " ", t, flags=re.I)
    t = re.sub(r"\((?:\d{1,2}:)?\d{1,2}:\d{2}\)", " ", t)
    # Remove simple time stamps 12:34 or 1:02:03
    t = re.sub(r"\b\d{1,2}:\d{2}(?::\d{2})?\b", " ", t)
    # Remove date-like stamps 03/12/2025
    t = re.sub(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", " ", t)
    # Remove speaker markers like 'John:' at start of lines
    t = re.sub(r"(?m)^[A-Z][A-Za-z0-9_\- ]{1,30}:\s*", "", t)
    # Remove fillers
    t = re.sub(r"(?i)\b(um+|uh+|er+|ah+)\b", " ", t)
    # Normalize bullets
    t = re.sub(r"(?m)^\s*[-•*]\s*", "- ", t)
    # Collapse whitespace
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def _ensure_gemini_configured() -> Optional[str]:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key or genai is None:
        return None
    try:
        genai.configure(api_key=api_key)
        return api_key
    except Exception:
        return None


def _gemini_model():
    # Prefer a fast and capable model
    return genai.GenerativeModel("gemini-1.5-flash")


def _chunk_text(text: str, max_chars: int = 12000) -> List[str]:
    """
    Split text into roughly max_chars chunks on sentence boundaries when possible.
    """
    if len(text) <= max_chars:
        return [text]
    sentences = sentence_split(text)
    chunks: List[str] = []
    buf = []
    size = 0
    for s in sentences:
        if size + len(s) + 1 > max_chars and buf:
            chunks.append(" ".join(buf))
            buf, size = [s], len(s) + 1
        else:
            buf.append(s)
            size += len(s) + 1
    if buf:
        chunks.append(" ".join(buf))
    return chunks


def generate_ai_summary(transcript: str, instructions: str) -> str:
    """
    Sends the transcript and instructions to the Gemini model to generate a summary.
    Automatically cleans transcript and handles long inputs by chunking and stitching.
    """
    # Ensure SDK configured
    if not _ensure_gemini_configured():
        raise RuntimeError("Gemini not configured: install google-generativeai and set GEMINI_API_KEY")

    clean = _clean_transcript(transcript)

    # If very long, summarize chunks first then ask for a final synthesis
    chunks = _chunk_text(clean)
    model = _gemini_model()

    if len(chunks) == 1:
        full_prompt = f"{instructions}\n\n--- TRANSCRIPT ---\n{chunks[0]}"
        resp = model.generate_content(full_prompt)
        return getattr(resp, "text", "") or ""

    partial_summaries: List[str] = []
    sub_prompt = (
        "You are summarizing a long meeting transcript chunk. "
        "Return concise markdown sections: Key Points, Decisions, Action Items with owners & deadlines if any."
    )
    for i, ch in enumerate(chunks, 1):
        p = f"{sub_prompt}\n\nCHUNK {i}/{len(chunks)}:\n{ch}"
        r = model.generate_content(p)
        partial_summaries.append(getattr(r, "text", "") or "")

    joined_partials = "\n\n".join(partial_summaries)
    final_prompt = (
        f"{instructions}\n\nYou are given partial summaries of chunks from a long transcript. "
        "Synthesize a single, coherent, non-redundant markdown summary with these sections: "
        "- Agenda (one line)\n- Key Discussion Points\n- Decisions\n- Action Items (with owners & deadlines)\n- Next Steps.\n\n"
        f"PARTIAL SUMMARIES:\n{joined_partials}"
    )
    final_resp = model.generate_content(final_prompt)
    return getattr(final_resp, "text", "") or ""


def summarize(text: str, instructions: str | None = None, max_sentences: int = 6) -> str:
    """
    Main entrypoint now prefers the AI path. Falls back to heuristic summarizer on error.
    """
    if not text or not (instructions and instructions.strip()):
        return "Error: Transcript and prompt cannot be empty."

    try:
        return generate_ai_summary(text, instructions.strip())
    except Exception:
        # Fallback to heuristic pipeline
        sentences = sentence_split(text)
        if not sentences:
            return ""
        filtered = apply_instruction_filters(sentences, instructions)
        scores = score_sentences(filtered)
        ranked = [s for s, _ in sorted(scores.items(), key=lambda kv: kv[1], reverse=True)]
        take = min(max_sentences, max(3, int(len(filtered) * 0.3)))
        selected = sorted(ranked[:take], key=lambda s: sentences.index(s))
        as_bullets = bool(re.search(r"bullet|point|list", instructions or "", re.I))
        if as_bullets:
            return "\n".join([f"• {s}" for s in selected])
        return " ".join(selected)
