"""PPTX metadata extractor — python-pptx core_properties + app.xml (same shape as .docx)."""
from __future__ import annotations

import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Any

_EP_NS = "{http://schemas.openxmlformats.org/officeDocument/2006/extended-properties}"


def extract_pptx(path: Path) -> dict[str, Any]:
    from pptx import Presentation

    out: dict[str, Any] = {
        "creator_app": None,
        "producer": None,
        "author": None,
        "last_modified_by": None,
        "created": None,
        "modified": None,
        "total_editing_time_minutes": None,
        "revision_count": None,
        "page_count": None,            # interpreted as slide count for .pptx
        "word_count": None,
        "paragraph_count": None,
        "title": None,
    }

    prs = Presentation(str(path))
    cp = prs.core_properties
    out["author"] = cp.author or None
    out["last_modified_by"] = cp.last_modified_by or None
    out["created"] = _iso(cp.created)
    out["modified"] = _iso(cp.modified)
    out["revision_count"] = cp.revision if cp.revision else None
    out["title"] = cp.title or None

    # The most reliable "page" count for a deck is the live slide count, regardless
    # of what Slides=N may say in app.xml (which can lag if the file was edited and
    # not properly saved by Office).
    try:
        out["page_count"] = len(prs.slides)
    except Exception:
        pass

    _merge_app_xml(path, out)

    return out


def _merge_app_xml(path: Path, out: dict[str, Any]) -> None:
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
        try:
            return int(t) if t is not None else None
        except ValueError:
            return None

    out["creator_app"] = _text("Application") or out["creator_app"]
    out["total_editing_time_minutes"] = _int("TotalTime")
    out["word_count"] = _int("Words")
    # Prefer the live slide count from python-pptx; fall back to Slides if missing.
    if out["page_count"] is None:
        out["page_count"] = _int("Slides")
    out["paragraph_count"] = _int("Paragraphs")


def _iso(dt) -> str | None:
    if dt is None:
        return None
    try:
        return dt.isoformat(timespec="seconds")
    except Exception:
        return str(dt)
