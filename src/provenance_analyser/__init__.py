"""provenance-analyser — document metadata / provenance signals for the lens family."""
from importlib.metadata import version as _v
from pathlib import Path

from .analyser import ProvenanceAnalyser
from .exceptions import ProvenanceAnalyserError
from .manifest import MANIFEST
from .schemas import ProvenanceAnalysis

__version__ = _v("provenance-analyser")
del _v


def analyse(path: str | Path) -> ProvenanceAnalysis:
    """Analyse a document's provenance/metadata signals.

    Module-level convenience wrapper around :meth:`ProvenanceAnalyser.analyse`.
    """
    return ProvenanceAnalyser().analyse(Path(path))


__all__ = [
    "ProvenanceAnalyser",
    "ProvenanceAnalysis",
    "ProvenanceAnalyserError",
    "analyse",
    "MANIFEST",
    "__version__",
]
