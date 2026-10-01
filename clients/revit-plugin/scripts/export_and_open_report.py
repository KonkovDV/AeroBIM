#!/usr/bin/env python3
"""Thin Revit-adjacent helper: analyze package via AeroBIM API and open UI deep-link.

Does not validate IFC locally — backend remains the source of truth (W2.7).
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
import webbrowser


def _post_json(url: str, body: dict[str, object], bearer: str | None) -> dict[str, object]:
    data = json.dumps(body).encode("utf-8")
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if bearer:
        headers["Authorization"] = f"Bearer {bearer}"
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=120) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"Unexpected response type: {type(payload)}")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export package → AeroBIM analyze → UI deep-link")
    parser.add_argument("--api-base", default="http://127.0.0.1:8080")
    parser.add_argument("--ui-base", default="http://127.0.0.1:5173")
    parser.add_argument("--ifc", required=True, help="Absolute path to IFC on the API host")
    parser.add_argument("--ids", default=None)
    parser.add_argument("--project", default=None)
    parser.add_argument("--discipline", default=None)
    parser.add_argument("--bearer", default=None)
    parser.add_argument("--open", action="store_true", help="Open deep-link in the default browser")
    args = parser.parse_args(argv)

    body: dict[str, object] = {"ifc_path": args.ifc}
    if args.ids:
        body["ids_path"] = args.ids
    if args.project:
        body["project_name"] = args.project
    if args.discipline:
        body["discipline"] = args.discipline

    url = args.api_base.rstrip("/") + "/v1/analyze/project-package"
    try:
        report = _post_json(url, body, args.bearer)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        print(f"API error {exc.code}: {detail}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"Request failed: {exc}", file=sys.stderr)
        return 1

    report_id = report.get("report_id")
    if not report_id:
        print(f"Response missing report_id: {report}", file=sys.stderr)
        return 1

    deep_link = f"{args.ui_base.rstrip('/')}/?report={report_id}"
    if args.project:
        deep_link += f"&project={urllib.parse.quote(args.project)}"
    print(deep_link)
    if args.open:
        webbrowser.open(deep_link)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
