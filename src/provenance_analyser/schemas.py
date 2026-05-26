"""Pydantic schemas for provenance-analyser output."""
from __future__ import annotations

from pydantic import BaseModel, Field


class ProvenanceAnalysis(BaseModel):
    """Provenance/metadata signals for a single document."""

    file_path: str
    file_format: str = Field(description="'docx' | 'pdf' | 'pptx' | 'xlsx'")
    file_size: int

    # Authoring app
    creator_app: str | None = Field(None, description="The app that wrote the file (Microsoft Office Word, LibreOffice, Pages, Google Docs export, …).")
    producer: str | None = Field(None, description="PDF only — the rendering engine (iText, Microsoft, Skia, Pandoc).")

    # Authorship
    author: str | None = None
    last_modified_by: str | None = None

    # Timeline (ISO 8601 strings as provided by the libraries; not normalised)
    created: str | None = None
    modified: str | None = None

    # Effort (Office formats only)
    total_editing_time_minutes: int | None = Field(
        None,
        description="Cumulative time the doc was open in edit mode (Office TotalTime field).",
    )
    revision_count: int | None = Field(
        None,
        description="Number of saves the authoring app recorded.",
    )

    # Size hints from metadata (not from text extraction).
    page_count: int | None = None
    word_count: int | None = None
    paragraph_count: int | None = None

    # AI-generation markers — conservative substring matches in creator/producer/title.
    ai_generation_markers: list[str] = Field(
        default_factory=list,
        description="Suspicious creator-string fragments (e.g. 'ChatGPT', 'Claude', 'gpt-').",
    )

    # Heuristic flags (composite — see analyser._compute_flags).
    flags: list[str] = Field(
        default_factory=list,
        description=(
            "Tags: edit_time_low_for_size, created_modified_same_minute, "
            "author_mismatch, ai_generation_marker, revision_count_zero, "
            "missing_metadata."
        ),
    )

    # Raw catch-all so unusual fields aren't silently dropped — debugging aid.
    raw: dict[str, str] = Field(
        default_factory=dict,
        description="Selected raw metadata key/value pairs for transparency.",
    )
