"""HTTP smoke tests — the family contract surface."""
from pathlib import Path

from fastapi.testclient import TestClient

from provenance_analyser.api import app
from provenance_analyser.manifest import MANIFEST


client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["version"] == MANIFEST["version"]


def test_manifest():
    r = client.get("/manifest")
    assert r.status_code == 200
    m = r.json()
    assert m["name"] == "provenance-analyser"
    assert m["auto_routable"] is False
    assert ".docx" in m["extensions"]


def test_analyse_empty_returns_422():
    r = client.post("/analyse", files={"file": ("x.docx", b"", "application/octet-stream")})
    assert r.status_code == 422


def test_analyse_real_docx(docx_with_metadata: Path):
    r = client.post(
        "/analyse",
        files={"file": (docx_with_metadata.name, docx_with_metadata.read_bytes(),
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["file_format"] == "docx"
    assert body["author"] == "Jane Student"
    assert body["total_editing_time_minutes"] == 45


def test_analyse_unsupported_returns_400(tmp_path: Path):
    f = tmp_path / "x.txt"
    f.write_bytes(b"plain text")
    r = client.post("/analyse", files={"file": ("x.txt", f.read_bytes(), "text/plain")})
    assert r.status_code == 400
