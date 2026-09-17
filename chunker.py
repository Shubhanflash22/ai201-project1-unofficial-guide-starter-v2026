"""
Stage 2 of the pipeline: splitting documents into chunks.

⚠️ THIS IS THE FILE YOU CHANGE IN MILESTONE 3.

`split_documents` below is deliberately plain. It cuts every document into
fixed-size pieces with a fixed overlap and pays no attention to where sentences
or paragraphs end. It works, and it is not good.

On a corpus of short posts it may not cut anything at all: `campus_life` comes
out as 88 documents and 88 chunks, because almost nothing in it reaches 800
characters. That is the baseline, not a bug - Milestone 3 is where you decide
whether one post should stay one chunk.

Your job in Milestone 3 is to replace the *body* of `split_documents` with a
strategy that fits the documents you actually read in Milestone 1. Keep the
name and the shape of what it returns - the rest of the pipeline calls it, and
your README has to name the function that produced your chunks.

If you get stuck for 30 minutes, `fallback_split` is the original. Switch back
to it, write down what you saw, and move on. That's a real observation about
your pipeline, not giving up.
"""

from dataclasses import dataclass

import config
from ingest import Document
import re


@dataclass
class Chunk:
    """One piece of one document."""

    text: str
    source: str        # which file it came from
    index: int         # which chunk within that file, starting at 0
    produced_by: str   # the function that made it - cite this in your README

    @property
    def label(self) -> str:
        return f"{self.source}#{self.index}"


def fallback_split(
    documents: list[Document],
    chunk_size: int | None = None,
    overlap: int | None = None,
) -> list[Chunk]:
    """
    The starter's original chunker. Fixed-size character windows with overlap.

    Keep this function. Milestone 3's stop rule points back at it, and having
    something to compare your own strategy against is useful in week 2.
    """
    chunk_size = chunk_size or config.CHUNK_SIZE
    overlap = overlap or config.CHUNK_OVERLAP

    if overlap >= chunk_size:
        raise ValueError("overlap has to be smaller than chunk_size")

    chunks: list[Chunk] = []
    for doc in documents:
        start = 0
        index = 0
        while start < len(doc.text):
            piece = doc.text[start : start + chunk_size].strip()
            if piece:
                chunks.append(
                    Chunk(
                        text=piece,
                        source=doc.source,
                        index=index,
                        produced_by="chunker.py::fallback_split",
                    )
                )
                index += 1
            start += chunk_size - overlap

    return chunks

MAX_CHUNK_CHARS = 900   # safety ceiling - no real section in this corpus needs it
OVERSIZE_OVERLAP = 100  # only used if MAX_CHUNK_CHARS is ever exceeded - distinct from config.CHUNK_OVERLAP, which only feeds fallback_split
MIN_STANDALONE_BODY = 40  # below this, a leading section is just a bare title


def _split_into_sections(text: str) -> tuple[str, list[tuple[str, str]]]:
    """
    Split one document's markdown into (heading, body) pairs.

    Every city_guides document opens with an H1 title, optionally followed by
    an intro paragraph, then a series of `## Heading` sections. This treats
    the intro (if any) as an "Overview" section so it's handled the same way
    as everything else.
    """
    text = text.replace("\r\n", "\n")
    parts = re.split(r"\n## ", text)

    title_block = parts[0]
    title_lines = title_block.split("\n", 1)
    title = title_lines[0].lstrip("#").strip()
    intro = title_lines[1].strip() if len(title_lines) > 1 else ""

    sections = [("Overview", intro)]
    for part in parts[1:]:
        lines = part.split("\n", 1)
        heading = lines[0].strip()
        body = lines[1].strip() if len(lines) > 1 else ""
        sections.append((heading, body))

    return title, sections


def _merge_short_leading_section(
    sections: list[tuple[str, str]]
) -> list[tuple[str, str]]:
    """
    Fold a near-empty leading section into the one that follows it.

    Several of the cross-cutting guides (guide_eating.md, guide_walking.md,
    guide_regional_transport.md, guide_seasons.md) open with nothing but a
    bare H1 title and no lead-in paragraph - that's exactly what produced the
    24-character fragment ("# Walking in the region") in the default
    fallback_split chunker. Folding it forward instead of emitting it as its
    own chunk removes that failure mode.
    """
    if len(sections) < 2:
        return sections
    heading, body = sections[0]
    if len(body) < MIN_STANDALONE_BODY:
        next_heading, next_body = sections[1]
        merged = f"{body}\n\n{next_body}".strip() if body else next_body
        return [(next_heading, merged)] + sections[2:]
    return sections


def _split_oversized(body: str) -> list[str]:
    """
    Sentence-boundary split for the rare section over MAX_CHUNK_CHARS.

    Nothing in city_guides currently triggers this (the longest section is
    709 characters), but it's here so a future, longer document degrades
    gracefully instead of getting cut mid-sentence like fallback_split does.
    """
    if len(body) <= MAX_CHUNK_CHARS:
        return [body]

    sentences = re.split(r"(?<=[.!?])\s+", body)
    pieces: list[str] = []
    current = ""
    for sentence in sentences:
        if current and len(current) + len(sentence) + 1 > MAX_CHUNK_CHARS:
            pieces.append(current.strip())
            tail = current[-OVERSIZE_OVERLAP :] if OVERSIZE_OVERLAP else ""
            current = f"{tail} {sentence}".strip()
        else:
            current = f"{current} {sentence}".strip()
    if current:
        pieces.append(current.strip())
    return pieces

def split_documents(documents: list[Document]) -> list[Chunk]:
    """
    Split documents on their own markdown headings rather than a fixed
    character count.

    Every city_guides document is already organised into `## ` sections
    (Getting there, Eat and drink, What to see...) and every real section
    comes in well under 800 characters - the longest across the whole corpus
    is 709. There's no need to cut mid-section; the author's own heading is a
    better, non-arbitrary boundary than a character count.

    Two adjustments on top of a plain per-heading split:

    - Each chunk is prefixed with its document's title. A section like
      "Eat and drink" never mentions the town's name inside its own text, so
      read alone it can't answer "which town does X" - the title makes the
      chunk self-contained.
    - A section with almost no body text gets folded into the one that
      follows it, instead of becoming its own chunk. See
      `_merge_short_leading_section` for why.
    """
    chunks: list[Chunk] = []

    for doc in documents:
        title, sections = _split_into_sections(doc.text)
        sections = _merge_short_leading_section(sections)

        index = 0
        for heading, body in sections:
            if not body:
                continue
            for piece in _split_oversized(body):
                chunk_text = f"{title} - {heading}\n\n{piece}"
                chunks.append(
                    Chunk(
                        text=chunk_text,
                        source=doc.source,
                        index=index,
                        produced_by="chunker.py::split_documents",
                    )
                )
                index += 1

    return chunks


def describe(chunks: list[Chunk]) -> str:
    """A one-line summary, printed after indexing."""
    if not chunks:
        return "0 chunks"
    lengths = [len(c.text) for c in chunks]
    return (
        f"{len(chunks)} chunks, "
        f"{sum(lengths) // len(lengths)} characters on average "
        f"(shortest {min(lengths)}, longest {max(lengths)}), "
        f"produced by {chunks[0].produced_by}"
    )


if __name__ == "__main__":
    from ingest import load_documents

    chunks = split_documents(load_documents())
    print(describe(chunks))
