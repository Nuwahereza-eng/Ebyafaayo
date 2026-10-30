"""Check Gemma's output against the transcript, so nothing invented reaches the family book.

Every extracted item must quote a sentence that really is in the transcript. Names and places
must actually appear in it. Anything that fails is marked ungrounded (and shown that way in the
UI); a clan or totem that fails is dropped, because those must never be guessed.
"""

import re
import unicodedata
from difflib import SequenceMatcher

from .schemas import StructuredMemory

MATCH_THRESHOLD = 0.8


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).lower()
    text = re.sub(r"[^\w\s']", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def split_sentences(transcript: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+|(?<=[.!?][\"”’'])\s+|\n+", transcript)
    return [p.strip() for p in parts if p.strip()]


class Grounder:
    def __init__(self, transcript: str):
        self.sentences = split_sentences(transcript)
        self.norm_sentences = [normalize(s) for s in self.sentences]
        self.norm_transcript = normalize(transcript)

    def find(self, quote: str) -> str | None:
        """Return the transcript sentence that `quote` came from, or None."""
        q = normalize(quote)
        if not q:
            return None
        for sent, norm in zip(self.sentences, self.norm_sentences):
            if q in norm or (len(norm) > 8 and norm in q):
                return sent
        if q in self.norm_transcript:
            # Quote spans a sentence break; return the sentences it touches.
            return " ".join(s for s, n in zip(self.sentences, self.norm_sentences) if n and n in q) or quote
        best, best_ratio = None, 0.0
        for sent, norm in zip(self.sentences, self.norm_sentences):
            ratio = SequenceMatcher(None, q, norm).ratio()
            if ratio > best_ratio:
                best, best_ratio = sent, ratio
        return best if best_ratio >= MATCH_THRESHOLD else None

    def mentions(self, phrase: str) -> bool:
        """True if every meaningful word of a name or place is in the transcript."""
        words = [w for w in normalize(phrase).split() if len(w) >= 3]
        if not words:
            return False
        transcript_words = set(self.norm_transcript.split())
        return all(w in transcript_words or w in self.norm_transcript for w in words)


def ground(memory: StructuredMemory, transcript: str) -> tuple[StructuredMemory, list[str]]:
    g = Grounder(transcript)
    notes: list[str] = []
    memory.changes_made = [c for c in memory.changes_made if normalize(c.original) != normalize(c.corrected)]

    def check(item, name: str | None = None) -> None:
        sentence = g.find(item.source_sentence)
        ok = sentence is not None and (name is None or g.mentions(name))
        if sentence:
            item.source_sentence = sentence
        item.grounded = ok
        if not ok and hasattr(item, "confidence"):
            item.confidence = "unclear"

    for p in memory.people:
        check(p, p.name)
    for p in memory.places:
        check(p, p.name)
    for t in memory.time_periods:
        check(t)
    for pr in memory.proverbs:
        check(pr)

    for field in ("clan", "totem"):
        attr = getattr(memory, field)
        if attr is None:
            continue
        if not attr.value.strip() or attr.value.strip().lower() in {"unclear", "unknown", "null", "none"}:
            setattr(memory, field, None)
            continue
        check(attr, attr.value)
        if not attr.grounded:
            notes.append(f"Removed {field} '{attr.value}': it is not clearly said in the transcript.")
            setattr(memory, field, None)

    ungrounded = sum(
        1 for item in [*memory.people, *memory.places, *memory.time_periods, *memory.proverbs] if not item.grounded
    )
    if ungrounded:
        notes.append(f"{ungrounded} item(s) could not be matched to the transcript. Please check or remove them.")
    return memory, notes


def similarity(a: str, b: str) -> float:
    """How close Gemma's cleaned Luganda is to the family's transcript (1.0 = identical)."""
    return round(SequenceMatcher(None, normalize(a), normalize(b)).ratio(), 3)


def remove_names(description: str, names: list[str]) -> tuple[str, list[str]]:
    """Drop any sentence of a photo description that names someone the family knows.

    Gemma may not say who is in a photo: it cannot know, and a wrong guess would be passed down.
    The family writes that part themselves.
    """
    words = {w for n in names for w in normalize(n).split() if len(w) > 2}
    kept, notes = [], []
    for sentence in split_sentences(description):
        capitalised = {normalize(w) for w in re.findall(r"\b[A-Z][\w']+", sentence)}  # names, not "photo"
        hit = words & capitalised
        if hit:
            notes.append(f"Removed a sentence that named someone ({', '.join(sorted(hit))}). Only the family says who is in a photo.")
        else:
            kept.append(sentence)
    return " ".join(kept), notes


LOOP = re.compile(r"\b(\w+)(?:\W+\1\b){2,}", re.IGNORECASE)  # the same word three times in a row


def clean_questions(questions: list[dict]) -> tuple[list[dict], list[str]]:
    """Drop repeated questions, and blank out a Luganda question where Gemma got stuck in a loop."""
    seen, kept, notes = set(), [], []
    for q in questions:
        key = normalize(q.get("english", ""))
        if not key or key in seen:
            continue
        seen.add(key)
        if LOOP.search(q.get("luganda", "")):
            q = {**q, "luganda": ""}
            notes.append(f"Gemma's Luganda for \"{q['english']}\" repeated itself, so it was removed. Please write it yourselves.")
        kept.append(q)
    return kept, notes
