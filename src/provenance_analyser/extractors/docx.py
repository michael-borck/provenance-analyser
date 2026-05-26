"""DOCX metadata extractor — python-docx core_properties + the app.xml extended properties.

python-docx exposes `core_properties` (Dublin-Core-style: author, created, modified, revision,
…), but the *extended* properties (Application, TotalTime, Words, Pages, Paragraphs) live in
`docProps/app.xml` inside the zip and aren't exposed by python-docx. We reach into the zip
directly for those — that's where TotalTime, the headline 'how long did they spend' signal,
lives.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Any

# OOXML namespace used by app.xml — bound at module level so the per-field XPath stays short.
_EP_NS = "{http://schemas.openxmlformats.org/officeDocument/2006/extended-properties}"


def extract_docx(path: Path) -> dict[str, Any]:
    """Return a uniform metadata dict for a .docx file."""
    from docx import Document

    out: dict[str, Any] = {
        "creator_app": None,
        "producer": None,           # not applicable for OOXML; here for symmetry with PDF
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

    # Core properties (Dublin Core).
    doc = Document(str(path))
    cp = doc.core_properties
    out["author"] = cp.author or None
    out["last_modified_by"] = cp.last_modified_by or None
    out["created"] = _iso(cp.created)
    out["modified"] = _iso(cp.modified)
    out["revision_count"] = cp.revision if cp.revision else None
    out["title"] = cp.title or None

    # Extended properties from docProps/app.xml — TotalTime, Application, Words, Pages, Paragraphs.
    _merge_app_xml(path, out)

    return out


def _merge_app_xml(path: Path, out: dict[str, Any]) -> None:
    """Pull the headline fields from docProps/app.xml directly (python-docx doesn't expose them)."""
    try:
        with zipfile.ZipFile(path) as z:
            with z.open("docProps/app.xml") as f:
                tree = ET.parse(f)
    except (KeyError, zipfile.BadZipFile, ET.ParseError):
        return
    root = tree.getroot()

    def _text(tag: str) -> str | None:
        node = root.find(f"{_EP_NS}{tag}")
        return node.text if (node is not None and node.text) else None

    def _int(tag: str) -> int | None:
        t = _text(tag)
        if t is None:
            return None
        try:
            return int(t)
        except ValueError:
            return None

    out["creator_app"] = _text("Application") or out["creator_app"]
    out["total_editing_time_minutes"] = _int("TotalTime")
    out["word_count"] = _int("Words")
    out["page_count"] = _int("Pages")
    out["paragraph_count"] = _int("Paragraphs")


def _iso(dt) -> str | None:
    """ISO 8601 with seconds, or None."""
    if dt is None:
        return None
    try:
        return dt.isoformat(timespec="seconds")
    except Exception:
        return str(dt)
