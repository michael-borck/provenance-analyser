"""Core provenance analyser — dispatch by extension, apply heuristic flags."""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from .exceptions import ProvenanceAnalyserError
from .extractors import extract_docx, extract_pdf, extract_pptx, extract_xlsx
from .schemas import ProvenanceAnalysis

# Conservative AI-generation markers — match in creator/producer/title strings.
# Substring matches; case-insensitive. Keep the list short to avoid false positives.
_AI_MARKERS = [
    "chatgpt", "openai", "gpt-4", "gpt-3", "claude",
    "anthropic", "gemini", "bard", "copilot", "llm",
]

# Heuristic threshold: words per minute of editing time at which we flag
# 'edit_time_low_for_size'. Typing speed ~40 wpm = 40 wpm sustained; below 5
# means a 1000-word doc claims <200 minutes which is plausible. Above 200 means
# a 1000-word doc had <5 minutes of editing time — implausible for original
# work. We pick a conservative 100 (5x typing speed) so we mostly flag pastes.
_WORDS_PER_MIN_SUSPICIOUS = 100

_DISPATCH = {
    ".docx": ("docx", extract_docx),
    ".pdf":  ("pdf",  extract_pdf),
    ".pptx": ("pptx", extract_pptx),
    ".xlsx": ("xlsx", extract_xlsx),
}


class ProvenanceAnalyser:
    """Read a document's provenance/metadata signals."""

    def analyse(self, path: str | Path) -> ProvenanceAnalysis:
        path = Path(path)
        if not path.exists():
            raise ProvenanceAnalyserError(f"File not found: {path}")
        suffix = path.suffix.lower()
        if suffix not in _DISPATCH:
            raise ProvenanceAnalyserError(
                f"Unsupported format: {suffix} (supported: {sorted(_DISPATCH)})"
            )

        file_format, extractor = _DISPATCH[suffix]
        try:
            raw = extractor(path)
        except Exception as e:
            raise ProvenanceAnalyserError(f"Failed to read metadata: {e}") from e

        markers = _detect_ai_markers(raw)
        flags = _compute_flags(raw, markers)

        # The 'raw' subdict on the response is a transparency aid — surface a
        # selected set of non-None fields so callers can audit our interpretation.
        transparency: dict[str, str] = {}
        for k in ("creator_app", "producer", "author", "last_modified_by",
                  "created", "modified", "title"):
            if raw.get(k) is not None:
                transparency[k] = str(raw[k])

        return ProvenanceAnalysis(
            file_path=str(path),
            file_format=file_format,
            file_size=path.stat().st_size,
            creator_app=raw.get("creator_app"),
            producer=raw.get("producer"),
            author=raw.get("author"),
            last_modified_by=raw.get("last_modified_by"),
            created=raw.get("created"),
            modified=raw.get("modified"),
            total_editing_time_minutes=raw.get("total_editing_time_minutes"),
            revision_count=raw.get("revision_count"),
            page_count=raw.get("page_count"),
            word_count=raw.get("word_count"),
            paragraph_count=raw.get("paragraph_count"),
            ai_generation_markers=markers,
            flags=flags,
            raw=transparency,
        )


def _detect_ai_markers(raw: dict) -> list[str]:
    """Conservative substring scan over creator/producer/title for known AI app names."""
    found: list[str] = []
    haystacks = [raw.get(k) for k in ("creator_app", "producer", "title")]
    for s in haystacks:
        if not s:
            continue
        s_lower = s.lower()
        for marker in _AI_MARKERS:
            if marker in s_lower and marker not in found:
                found.append(marker)
    return found


def _compute_flags(raw: dict, ai_markers: list[str]) -> list[str]:
    """Aggregate heuristic flags. Empty list = nothing flagged."""
    flags: list[str] = []

    # Mostly-empty metadata is itself a soft signal (esp. for student work).
    if not any(raw.get(k) for k in ("author", "creator_app", "created", "modified")):
        flags.append("missing_metadata")

    # Author vs last_modified_by mismatch.
    a = (raw.get("author") or "").strip()
    lm = (raw.get("last_modified_by") or "").strip()
    if a and lm and a != lm:
        flags.append("author_mismatch")

    # Created and modified within the same minute → almost certainly fresh export / paste.
    created = _parse_iso_or_pdf(raw.get("created"))
    modified = _parse_iso_or_pdf(raw.get("modified"))
    if created and modified:
        if abs((modified - created).total_seconds()) < 60:
            flags.append("created_modified_same_minute")

    # Office's revision counter never incremented — typical for a single-save export.
    revision = raw.get("revision_count")
    if revision is not None and revision == 0:
        flags.append("revision_count_zero")

    # Edit time vs size — only meaningful when both fields are present.
    edit_time = raw.get("total_editing_time_minutes")
    words = raw.get("word_count")
    if edit_time is not None and words is not None and edit_time > 0:
        wpm = words / edit_time
        if wpm > _WORDS_PER_MIN_SUSPICIOUS:
            flags.append("edit_time_low_for_size")

    if ai_markers:
        flags.append("ai_generation_marker")

    return flags


def _parse_iso_or_pdf(s: str | None):
    """Parse either an ISO timestamp (OOXML) or a PDF D:YYYYMMDDHHMMSS… string."""
    if not s:
        return None
    s = str(s).strip()
    # PDF dates start with D:
    if s.startswith("D:"):
        digits = re.sub(r"\D", "", s[2:])[:14]
        if len(digits) >= 12:  # YYYYMMDDHHMM
            try:
                return datetime.strptime(digits.ljust(14, "0"), "%Y%m%d%H%M%S")
            except ValueError:
                return None
        return None
    # ISO timestamps from OOXML — strip 'Z' if naive parsing needed.
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None
