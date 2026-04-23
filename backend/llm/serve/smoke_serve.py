from __future__ import annotations

import argparse
import json
import threading
import time
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import ProxyHandler, Request, build_opener, urlopen


class _SmokeHandler(BaseHTTPRequestHandler):
    def _write_json(self, status_code: int, payload: dict[str, object]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self._write_json(200, {"status": "ok", "service": "aerobim-ft-smoke"})
            return
        self._write_json(404, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/v1/chat/completions":
            self._write_json(404, {"error": "not_found"})
            return

        length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
        payload = json.loads(raw_body)
        model = payload.get("model") or "aerobim-ft-smoke-model"

        self._write_json(
            200,
            {
                "id": "chatcmpl-aerobim-ft-smoke",
                "object": "chat.completion",
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "finish_reason": "stop",
                        "message": {
                            "role": "assistant",
                            "content": "AeroBIM FT serve smoke response",
                        },
                    }
                ],
            },
        )

    def log_message(self, format: str, *args: object) -> None:  # noqa: A003
        return


def request_json(url: str, method: str = "GET", payload: dict[str, object] | None = None) -> tuple[int, dict[str, object]]:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
    request = Request(url=url, method=method, data=data)
    if data is not None:
        request.add_header("Content-Type", "application/json")

    hostname = urlparse(url).hostname
    if hostname in {"127.0.0.1", "localhost"}:
        opener = build_opener(ProxyHandler({}))
        response_ctx = opener.open(request, timeout=5)
    else:
        response_ctx = urlopen(request, timeout=5)  # noqa: S310

    with response_ctx as response:
        raw = response.read().decode("utf-8")
        body = json.loads(raw) if raw else {}
        return int(response.status), body


def wait_for_health(base_url: str, timeout_seconds: float = 5.0) -> None:
    deadline = time.monotonic() + timeout_seconds
    last_error: Exception | None = None

    while time.monotonic() < deadline:
        try:
            status, body = request_json(f"{base_url}/health")
            if status == 200 and body.get("status") == "ok":
                return
        except Exception as error:  # pragma: no cover - retry path
            last_error = error
        time.sleep(0.1)

    raise TimeoutError(f"serve smoke health probe timed out: {last_error}")


def run_serve_smoke(output_path: Path) -> dict[str, object]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), _SmokeHandler)
    port = int(server.server_address[1])
    base_url = f"http://127.0.0.1:{port}"
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    checks: list[dict[str, object]] = []
    try:
        wait_for_health(base_url)
        health_status, health_body = request_json(f"{base_url}/health")
        checks.append(
            {
                "name": "health_endpoint",
                "passed": health_status == 200 and health_body.get("status") == "ok",
                "details": json.dumps({"status": health_status, "body": health_body}, ensure_ascii=False),
            }
        )

        completion_status, completion_body = request_json(
            f"{base_url}/v1/chat/completions",
            method="POST",
            payload={
                "model": "aerobim-ft-smoke-model",
                "messages": [{"role": "user", "content": "ping"}],
            },
        )
        choices = completion_body.get("choices") if isinstance(completion_body, dict) else None
        message_content = (
            choices[0].get("message", {}).get("content")
            if isinstance(choices, list) and choices and isinstance(choices[0], dict)
            else None
        )
        checks.append(
            {
                "name": "openai_completion_endpoint",
                "passed": completion_status == 200 and message_content == "AeroBIM FT serve smoke response",
                "details": json.dumps(
                    {"status": completion_status, "content": message_content},
                    ensure_ascii=False,
                ),
            }
        )
    finally:
        server.shutdown()
        server.server_close()

    status = "APPROVED" if all(check["passed"] for check in checks) else "DEGRADED"
    report = {
        "artifact_type": "aerobim_ft_serve_smoke_report",
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "status": status,
        "port": port,
        "checks": checks,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="AeroBIM FT serve smoke")
    parser.add_argument("--output", type=Path, default=Path("llm/artifacts/serve/smoke_serve_report_v1.json"))
    args = parser.parse_args()

    report = run_serve_smoke(args.output.resolve())
    print(json.dumps({"status": report["status"], "output": str(args.output.resolve())}, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["status"] == "APPROVED" else 1)


if __name__ == "__main__":
    main()
