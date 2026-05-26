"""Per-format metadata extractors. Each module exposes `extract(path: Path) -> dict[str, Any]`
returning a uniform shape (creator_app, author, last_modified_by, created, modified, …) so the
analyser's downstream logic doesn't need per-format branches.

Each extractor MUST tolerate missing fields — student-submitted documents are often half-
configured. Return `None` for missing values; never raise on a recoverable read.
"""
from .docx import extract_docx
from .pdf import extract_pdf
from .pptx import extract_pptx
from .xlsx import extract_xlsx

__all__ = ["extract_docx", "extract_pdf", "extract_pptx", "extract_xlsx"]
