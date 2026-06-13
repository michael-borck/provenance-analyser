# basic_usage

Minimal ways to run provenance-analyser.

## Install

```bash
pip install provenance-analyser
```

## CLI

```bash
provenance-analyser draft.docx --json
```

Accepts `.docx`, `.pdf`, `.pptx`, `.xlsx`. Without `--json` it prints a human-readable summary.

## Python

```python
from provenance_analyser import ProvenanceAnalyser

result = ProvenanceAnalyser().analyse("draft.docx")
print(result.model_dump_json(indent=2))
```

## HTTP

```bash
provenance-analyser serve            # http://localhost:8014
curl -F file=@draft.docx http://localhost:8014/analyse
```
