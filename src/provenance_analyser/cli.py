"""CLI entry point for provenance-analyser."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> None:
    from lens_contract import run_contract_subcommands

    from .manifest import MANIFEST

    if run_contract_subcommands(
        MANIFEST,
        app_path="provenance_analyser.api:app",
        default_port=8014,
        env_prefix="PROVENANCE_ANALYSER",
    ):
        return

    parser = argparse.ArgumentParser(
        prog="provenance-analyser",
        description="Document provenance/metadata analysis — .docx / .pdf / .pptx / .xlsx",
        epilog="subcommands: `serve` (HTTP API on port 8014), `manifest` (capability manifest)",
    )
    parser.add_argument("file", type=Path, help=".docx / .pdf / .pptx / .xlsx")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Output raw JSON")
    args = parser.parse_args()

    _run(args)


def _run(args) -> None:
    from .analyser import ProvenanceAnalyser
    from .exceptions import ProvenanceAnalyserError

    try:
        result = ProvenanceAnalyser().analyse(args.file)
    except ProvenanceAnalyserError as e:
        if args.as_json:
            print(json.dumps({"error": str(e)}), file=sys.stderr)
        else:
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.as_json:
        print(result.model_dump_json(indent=2))
        return

    _print_summary(result)


def _print_summary(result) -> None:
    print(f"File:       {result.file_path}")
    print(f"Format:     .{result.file_format}  ({result.file_size:,} bytes)")
    if result.creator_app:
        print(f"Creator:    {result.creator_app}")
    if result.producer:
        print(f"Producer:   {result.producer}")
    if result.author:
        print(f"Author:     {result.author}")
    if result.last_modified_by and result.last_modified_by != result.author:
        print(f"Last mod:   {result.last_modified_by}")
    if result.created:
        print(f"Created:    {result.created}")
    if result.modified:
        print(f"Modified:   {result.modified}")
    if result.total_editing_time_minutes is not None:
        h, m = divmod(result.total_editing_time_minutes, 60)
        if h:
            print(f"Edit time:  {result.total_editing_time_minutes} min  ({h}h {m}m)")
        else:
            print(f"Edit time:  {m} min")
    if result.revision_count is not None:
        print(f"Revisions:  {result.revision_count}")
    if result.page_count is not None:
        # .pptx → 'slide_count', .xlsx → 'sheet_count', otherwise 'pages'
        label = {"pptx": "Slides", "xlsx": "Sheets"}.get(result.file_format, "Pages")
        print(f"{label}:     {result.page_count}")
    if result.word_count is not None:
        print(f"Words:      {result.word_count:,}")
    if result.ai_generation_markers:
        print(f"AI markers: {', '.join(result.ai_generation_markers)}")
    if result.flags:
        print()
        print("Flags:")
        for f in result.flags:
            print(f"  - {f}")


if __name__ == "__main__":
    main()
