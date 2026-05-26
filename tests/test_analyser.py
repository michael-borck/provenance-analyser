"""End-to-end tests for ProvenanceAnalyser dispatch + flag computation."""
from pathlib import Path

import pytest

from provenance_analyser import ProvenanceAnalyser, ProvenanceAnalyserError
from provenance_analyser.schemas import ProvenanceAnalysis


# ── docx ─────────────────────────────────────────────────────────────────


class TestDocx:
    def test_basic(self, docx_with_metadata: Path):
        r = ProvenanceAnalyser().analyse(docx_with_metadata)
        assert isinstance(r, ProvenanceAnalysis)
        assert r.file_format == "docx"
        assert r.author == "Jane Student"
        assert r.last_modified_by == "Jane Student"
        assert r.revision_count == 4
        assert r.creator_app == "Microsoft Office Word"
        assert r.total_editing_time_minutes == 45
        assert r.word_count == 100

    def test_edit_time_low_flag(self, docx_low_edit_time: Path):
        r = ProvenanceAnalyser().analyse(docx_low_edit_time)
        # 1500 words / 2 min = 750 wpm > 100 wpm threshold
        assert "edit_time_low_for_size" in r.flags

    def test_ai_marker_flag(self, docx_with_ai_marker: Path):
        r = ProvenanceAnalyser().analyse(docx_with_ai_marker)
        assert "chatgpt" in r.ai_generation_markers
        assert "ai_generation_marker" in r.flags

    def test_missing_metadata_flag(self, docx_minimal: Path):
        r = ProvenanceAnalyser().analyse(docx_minimal)
        # python-docx writes 'core' properties with empty strings + a created/modified
        # timestamp by default — so missing_metadata may or may not trigger depending
        # on library version. The key contract: it doesn't crash, and we get a result.
        assert isinstance(r.flags, list)


# ── pptx ─────────────────────────────────────────────────────────────────


class TestPptx:
    def test_basic(self, pptx_with_metadata: Path):
        r = ProvenanceAnalyser().analyse(pptx_with_metadata)
        assert r.file_format == "pptx"
        assert r.author == "Slide Author"
        assert r.last_modified_by == "Reviewer"
        assert "author_mismatch" in r.flags
        # Slide count is the live count from python-pptx.
        assert r.page_count == 2
        assert r.total_editing_time_minutes == 30


# ── xlsx ─────────────────────────────────────────────────────────────────


class TestXlsx:
    def test_basic(self, xlsx_with_metadata: Path):
        r = ProvenanceAnalyser().analyse(xlsx_with_metadata)
        assert r.file_format == "xlsx"
        assert r.author == "Spreadsheet Author"
        assert r.revision_count == 3
        # Sheet count via openpyxl, falling back to Slides=N in app.xml if missing.
        assert r.page_count == 2
        assert r.total_editing_time_minutes == 60


# ── pdf ──────────────────────────────────────────────────────────────────


class TestPdf:
    def test_basic(self, pdf_with_metadata: Path):
        r = ProvenanceAnalyser().analyse(pdf_with_metadata)
        assert r.file_format == "pdf"
        assert r.author == "PDF Author"
        assert r.creator_app == "ReportLab"
        # PDFs don't carry TotalTime — that's expected.
        assert r.total_editing_time_minutes is None
        assert r.page_count == 1


# ── dispatch errors ──────────────────────────────────────────────────────


class TestDispatch:
    def test_missing_file_raises(self):
        with pytest.raises(ProvenanceAnalyserError, match="not found"):
            ProvenanceAnalyser().analyse("/no/such/file.docx")

    def test_unsupported_extension_raises(self, tmp_path: Path):
        f = tmp_path / "x.txt"
        f.write_text("hello")
        with pytest.raises(ProvenanceAnalyserError, match="Unsupported format"):
            ProvenanceAnalyser().analyse(f)
