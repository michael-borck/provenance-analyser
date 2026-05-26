"""FastAPI service — provenance-analyser."""
from __future__ import annotations

from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from lens_contract import add_contract_routes, add_cors, upload_tempfile

from .analyser import ProvenanceAnalyser
from .exceptions import ProvenanceAnalyserError
from .manifest import MANIFEST
from .schemas import ProvenanceAnalysis

_lens = ProvenanceAnalyser()

app = FastAPI(
    title="provenance-analyser",
    description="Document provenance/metadata analysis — creator app, editing time, authorship, AI-gen markers",
    version=MANIFEST["version"],
    docs_url="/docs",
    redoc_url="/redoc",
)

add_contract_routes(app, MANIFEST)
add_cors(app, env_prefix="PROVENANCE_ANALYSER")


@app.get("/")
async def root() -> dict[str, Any]:
    return {
        "service": "provenance-analyser",
        "version": MANIFEST["version"],
        "status": "running",
        "endpoints": {"health": "/health", "manifest": "/manifest", "analyse": "/analyse"},
    }


@app.post("/analyse", response_model=ProvenanceAnalysis)
async def analyse(
    file: UploadFile = File(..., description=".docx / .pdf / .pptx / .xlsx"),
) -> ProvenanceAnalysis:
    content = await file.read()
    if not content:
        raise HTTPException(status_code=422, detail="Empty file")
    with upload_tempfile(content, file.filename) as tmp_path:
        try:
            return _lens.analyse(tmp_path)
        except ProvenanceAnalyserError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
