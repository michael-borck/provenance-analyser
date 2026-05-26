"""CLI smoke tests."""
import json
import subprocess
import sys
from pathlib import Path


def _run(*args) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "provenance_analyser.cli", *map(str, args)],
        capture_output=True,
        text=True,
    )


def test_missing_file_nonzero(tmp_path: Path):
    r = _run(tmp_path / "nope.docx")
    assert r.returncode != 0


def test_human_summary(docx_with_metadata: Path):
    r = _run(docx_with_metadata)
    assert r.returncode == 0, r.stderr
    assert "Format:" in r.stdout
    assert "Creator:" in r.stdout
    assert "Edit time:" in r.stdout


def test_json_output(docx_with_metadata: Path):
    r = _run(docx_with_metadata, "--json")
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)
    assert data["file_format"] == "docx"
    assert data["author"] == "Jane Student"


def test_manifest_subcommand():
    r = _run("manifest")
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)
    assert data["name"] == "provenance-analyser"
