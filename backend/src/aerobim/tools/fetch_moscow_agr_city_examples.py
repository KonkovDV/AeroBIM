"""Download city-published Moscow AGR example IFCs into gitignored ``.local/``.

Does not vendor binaries into git. Does not close RT-001.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import ssl
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aerobim.domain.checkpoint import CHECKPOINT
from aerobim.tools.benchmark_project_package import repo_root
from aerobim.tools.moscow_agr_city_examples import (
    CLAIM_BOUNDARY,
    CLAIM_LEVEL,
    ifc_dir,
    load_manifest,
    local_root,
    pin_path,
    sha256_bytes,
    sha256_file,
)

USER_AGENT = "AeroBIM-moscow-agr-fetch/1.0 (research pin; not redistribution)"


def _ssl() -> ssl.SSLContext:
    return ssl.create_default_context()


def download_file(url: str, dest: Path) -> dict[str, Any]:
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    digest_size = 0
    hasher = hashlib.sha256()
    with urllib.request.urlopen(req, context=_ssl(), timeout=600) as resp, dest.open("wb") as out:
        while True:
            chunk = resp.read(1024 * 1024)
            if not chunk:
                break
            out.write(chunk)
            hasher.update(chunk)
            digest_size += len(chunk)
    return {"bytes": digest_size, "sha256": hasher.hexdigest(), "url": url}


def write_notice(root: Path) -> None:
    text = "\n".join(
        [
            "# City AGR example IFCs — local pin",
            "",
            "Publisher: knowledge base stroimprosto.mos.ru (article cim-agr).",
            "AeroBIM does not claim authorship.",
            "",
            "Allowed: cite the article; aggregate engine metrics.",
            "Not allowed here: commit IFC/TRM binaries to git; claim Samolet accuracy;",
            "claim RT-001 / RT-002b / RT-003 closed; treat this as a PD pack.",
            "",
            CLAIM_BOUNDARY,
            "",
        ]
    )
    (local_root(root) / "NOTICE.md").write_text(text, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-size-drift", action="store_true")
    parser.add_argument("--force", action="store_true", help="Re-download even if size matches")
    args = parser.parse_args(argv)
    root = repo_root()
    manifest = load_manifest(root)
    dest_dir = ifc_dir(root)
    dest_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    for entry in manifest.get("files") or []:
        if not isinstance(entry, dict):
            continue
        name = str(entry["local_name"])
        url = str(entry["url"])
        expected = int(entry["expected_bytes"])
        dest = dest_dir / name
        cached = dest.is_file() and dest.stat().st_size == expected and not args.force
        if cached:
            meta = {"bytes": expected, "sha256": sha256_file(dest), "url": url}
        else:
            try:
                meta = download_file(url, dest)
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                errors.append(f"{name}: {exc}")
                continue
        size_ok = meta["bytes"] == expected
        if not size_ok and not args.allow_size_drift:
            errors.append(f"{name}: size {meta['bytes']} != expected {expected}")
        rows.append(
            {
                "id": entry.get("id"),
                "local_name": name,
                "url": url,
                "bytes": meta["bytes"],
                "expected_bytes": expected,
                "size_ok": size_ok,
                "cached": cached,
                "sha256": meta["sha256"],
                "path": dest.relative_to(root).as_posix(),
            }
        )
    pin: dict[str, Any] = {
        "schema_version": "1.0.0",
        "artifact_type": "moscow_agr_city_examples_pin",
        "claim_level": CLAIM_LEVEL,
        "claim_boundary": CLAIM_BOUNDARY,
        "closes_rt001": False,
        "closes_rt002b": False,
        "closes_rt003": False,
        "checkpoint": CHECKPOINT,
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "source_page": manifest.get("source_page"),
        "files": rows,
        "errors": errors,
    }
    encoded = json.dumps(pin, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    pin["content_sha256"] = sha256_bytes(encoded)
    pin_file = pin_path(root)
    pin_file.parent.mkdir(parents=True, exist_ok=True)
    pin_file.write_text(json.dumps(pin, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_notice(root)
    print(json.dumps({"status": "ERROR" if errors else "OK", "files": len(rows), "errors": errors}))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
