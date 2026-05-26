"""Capability manifest for the lens family (consumed by auto-analyser)."""
from __future__ import annotations

from lens_contract import make_manifest

# Explicit-only: .docx/.pdf/.pptx/.xlsx already auto-route to document/records for
# their content. This member is a different *interpretation* of the same bytes —
# provenance/metadata rather than content. Invoke deliberately.
MANIFEST = make_manifest(
    name="provenance-analyser",
    accepts=["document-metadata", "provenance"],
    extensions=[".docx", ".pdf", ".pptx", ".xlsx"],
    auto_routable=False,
    produces="ProvenanceAnalysis",
)
