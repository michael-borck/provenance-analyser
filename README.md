# provenance-analyser

**Document provenance signals** — the [lens-family](https://github.com/michael-borck/lens-analysers)
member that reads a document's *metadata* (who authored it, how long they spent in it, what app
made it, what's been flagged) rather than its content.

> `document-analyser` reads the *text*; `records-analyser` reads the *data*; this one reads the
> *provenance* — the same `.docx`/`.pdf`/`.pptx`/`.xlsx` bytes interpreted as a record of
> authorship and effort. Generalises `image-analyser`'s C2PA signal (which surfaces AI-gen
> markers for images) to the document formats. **Explicit-only** — those extensions continue
> to auto-route to document/records by default.

The single most cited signal here is **Office's `TotalTime` field** — the cumulative editing
time in minutes that Word/PowerPoint/Excel track per document. A 50-page paper with 23 minutes
of editing time is a story; a 10-page paper with 14 hours is another.

## Install

```bash
pip install provenance-analyser
```

## Use

**Python:**

```python
from provenance_analyser import ProvenanceAnalyser

result = ProvenanceAnalyser().analyse("essay.docx")
print(result.creator_app)                  # "Microsoft Office Word"
print(result.total_editing_time_minutes)   # 23
print(result.revision_count)               # 4
print(result.author)                       # "Jane Student"
print(result.last_modified_by)             # "Jane Student"
print(result.flags)                        # ["edit_time_low_for_size"]
```

**CLI:**

```bash
provenance-analyser essay.docx          # human summary
provenance-analyser essay.pdf --json    # raw JSON
provenance-analyser serve               # HTTP API on port 8014
provenance-analyser manifest            # capability manifest
```

**HTTP** (`provenance-analyser serve` on port 8014):

```bash
curl -F file=@essay.docx http://localhost:8014/analyse
```

## Signals

- **Creator** — `creator_app` (Microsoft Office Word / Google Docs / LibreOffice / Pages /
  Pandoc / iText), `producer` (PDF only — the engine that wrote the file).
- **Authorship** — `author`, `last_modified_by`. A mismatch is itself a signal.
- **Timeline** — `created`, `modified`. Created-and-modified-within-N-seconds is suspicious.
- **Effort (Office only)** — `total_editing_time_minutes` (the cumulative time the doc was
  open in edit mode), `revision_count` (number of saves).
- **Size hints (from metadata, not from extraction)** — `page_count`, `word_count`,
  `paragraph_count`.
- **AI-gen markers** — explicit hints in the creator/producer/title strings (`ChatGPT`,
  `Claude`, `LLM`, `gpt`, etc.). Conservative — false negatives expected, false positives rare.
- **Flags** — heuristic warnings: `edit_time_low_for_size`, `created_modified_same_minute`,
  `author_mismatch`, `ai_generation_marker`, `revision_count_zero`.

## Supported formats

| Format | Source of metadata |
|---|---|
| `.docx` | python-docx `core_properties` + `docProps/app.xml` (TotalTime, Application, Words) |
| `.pptx` | python-pptx `core_properties` + `docProps/app.xml` |
| `.xlsx` | openpyxl `workbook.properties` + `docProps/app.xml` |
| `.pdf` | pypdf `reader.metadata` (Creator, Producer, CreationDate, ModDate, Author) |

For **images**, use [image-analyser](https://github.com/michael-borck/image-analyser) directly —
it already covers EXIF, IPTC, XMP, and C2PA. This member is for office documents and PDFs.

## The family

Part of the [lens analyser family](https://github.com/michael-borck/lens-analysers).

| What you want | Use |
|---|---|
| The document's *text* | **document-analyser** |
| The document's *provenance* | **provenance-analyser** (this) |
| An image's metadata (EXIF / C2PA) | **image-analyser** |
| Any file → right engine | **auto-analyser** |

## Triangulation

The interesting signal is rarely one number alone. A polished essay
(`document-analyser`: high readability) + 18 minutes total editing time
(`provenance-analyser`) + an AI chat with low critical-thinking
(`conversation-analyser`) tells a different story than the same essay with
14 hours of editing time. Each member is one input; you compose them.

## Limits

- `TotalTime` is set by the authoring app — closed Office stops counting; idle time in an
  open doc still counts. It's a strong relative signal across student submissions, not an
  absolute clock.
- PDFs converted from another format (Word → PDF) keep the *converter's* metadata, not the
  original author's; this is correct behaviour but worth knowing.
- AI-generation markers are conservative — explicit creator-string matches only. Absence is
  not evidence of human authorship.

## License

MIT
