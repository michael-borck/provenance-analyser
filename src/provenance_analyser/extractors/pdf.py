"""PDF metadata extractor — pypdf Reader.metadata.

PDFs don't carry an Office-style 'TotalTime' (the editing-time signal), but they DO carry
useful provenance: Creator (the app that authored), Producer (the engine that wrote the file —
often a hint at conversion), Author, CreationDate, ModDate, Title.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any


def extract_pdf(path: Path) -> dict[str, Any]:
    from pypdf import PdfReader

    out: dict[str, Any] = {
        "creator_app": None,
        "producer": None,
        "author": None,
        "last_modified_by": None,
        "created": None,
        "modified": None,
        "total_editing_time_minutes": None,
        "revision_count": None,
        "page_count": None,
        "word_count": None,
        "paragraph_count": None,
        "title": None,
    }

    reader = PdfReader(str(path))
    md = reader.metadata or {}

    # pypdf wraps strings in PdfString (subclass of str); coerce defensively.
    def _str(k: str) -> str | None:
        v = md.get(k) if hasattr(md, "get") else None
        if v is None:
            return None
        s = str(v).strip()
        return s or None

    out["creator_app"] = _str("/Creator")
    out["producer"] = _str("/Producer")
    out["author"] = _str("/Author")
    out["title"] = _str("/Title")
    out["created"] = _str("/CreationDate")
    out["modified"] = _str("/ModDate")

    try:
        out["page_count"] = len(reader.pages)
    except Exception:
        pass

    return out
