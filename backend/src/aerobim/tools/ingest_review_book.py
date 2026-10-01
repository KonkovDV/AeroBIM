"""Ingest RD review books by structure into .local/. Never samples/customer."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from aerobim.domain.customer_review_book import (
    ReviewBookError,
    assert_output_path_allowed,
    dedupe_books,
    parse_review_book,
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ingest review books (structure, not filename)")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--coverage-hash", default="")
    parser.add_argument("--expected-coverage-hash", default="")
    parser.add_argument("--rd-ifc", action="store_true")
    args = parser.parse_args(argv)
    repo = repo_root()
    assert_output_path_allowed(args.output, repo=repo)
    args.output.mkdir(parents=True, exist_ok=True)
    paths = sorted(
        p
        for p in args.input.rglob("*")
        if p.suffix.lower() in {".xlsx", ".xlsm"}
        and (
            "замечан" in p.name.casefold()
            or "типов" in p.name.casefold()
            or "замечан" in p.as_posix().casefold()
        )
    )
    unique, duplicates = dedupe_books(paths)
    books = []
    skipped = 0
    for path in unique:
        try:
            books.append(
                parse_review_book(
                    path,
                    rd_ifc_present=args.rd_ifc,
                    coverage_hash=args.coverage_hash or None,
                    expected_coverage_hash=args.expected_coverage_hash or None,
                )
            )
        except (ReviewBookError, OSError, ValueError):
            skipped += 1
            continue
    manifest = {
        "artifact_type": "review_book_ingest_manifest",
        "dataset_status": "draft",
        "adjudicators": 1,
        "publishable": False,
        "unique_books": len(unique),
        "duplicate_files": duplicates,
        "skipped_not_review_book": skipped,
        "requirement_rows": sum(int(book.get("requirement_count") or 0) for book in books),
        "source_kinds": sorted({str(book.get("source_kind")) for book in books}),
    }
    (args.output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    for book in books:
        name = f"{book['book_sha'][:16]}-{book['source_kind']}.json"
        (args.output / name).write_text(
            json.dumps(book, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    print(
        json.dumps(
            {
                "unique_books": len(unique),
                "duplicate_files": duplicates,
                "parsed": len(books),
                "skipped_not_review_book": skipped,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
