"""Canonical public-surface tests — uniform across the lens -analyser family."""
import provenance_analyser
from provenance_analyser import (
    MANIFEST,
    ProvenanceAnalyser,
    ProvenanceAnalyserError,
    ProvenanceAnalysis,
    __version__,
    analyse,
)


def test_canonical_names_import():
    assert ProvenanceAnalyser is not None
    assert ProvenanceAnalysis is not None
    assert ProvenanceAnalyserError is not None
    assert MANIFEST is not None


def test_analyse_is_callable():
    assert callable(analyse)


def test_manifest_name():
    assert MANIFEST["name"] == "provenance-analyser"


def test_version_is_str():
    assert isinstance(__version__, str)


def test_all_lists_canonical_surface():
    expected = {
        "ProvenanceAnalyser",
        "ProvenanceAnalysis",
        "ProvenanceAnalyserError",
        "analyse",
        "MANIFEST",
        "__version__",
    }
    assert expected <= set(provenance_analyser.__all__)
