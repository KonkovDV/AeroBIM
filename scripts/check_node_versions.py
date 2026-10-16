#!/usr/bin/env python3
"""Keep the Node.js version consistent across the repo (AER-10).

Checks, with no third-party dependencies:
1. `.nvmrc` and `.node-version` hold the same exact X.Y.Z version.
2. The lowest version allowed by `frontend/package.json` `engines.node` equals it.
3. That floor satisfies `engines.node` of every package in `frontend/package-lock.json`,
   so `npm ci` under `engine-strict=true` cannot fail on a supported Node.
4. The dev container Node feature pins the same version.
5. Every `actions/setup-node` step reads `node-version-file: .nvmrc` (no literal versions).
6. User-facing docs and launchers do not advertise a stale minimum.

CI also installs at exactly this floor (`.nvmrc`) with `engine-strict`, which is the
end-to-end guard; this script catches drift without a network install.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
Version = tuple[int, int, int]

_STALE_DOC_FILES = (
    "README.md",
    "README.ru.md",
    "frontend/README.md",
    "start.sh",
    "start.bat",
    "start.ps1",
    "deploy/demo/setup-demo.sh",
    "deploy/demo/setup-demo.ps1",
    "deploy/demo/setup-demo.bat",
    "deploy/demo/README.md",
    "docs/demo-deployment-2026.md",
    ".devcontainer/README.md",
)


def parse_version(text: str) -> Version:
    m = re.fullmatch(r"v?(\d+)(?:\.(\d+|x|\*))?(?:\.(\d+|x|\*))?", text.strip())
    if not m:
        raise ValueError(f"unparseable version: {text!r}")
    parts = [p if p and p not in ("x", "*") else "0" for p in m.groups()]
    return (int(parts[0]), int(parts[1]), int(parts[2]))


def _partial(text: str) -> tuple[Version, int]:
    """Return (version, number of explicitly given components)."""
    raw = text.strip().lstrip("v")
    given = len([p for p in raw.split(".") if p not in ("", "x", "*")])
    return parse_version(raw), given


def _satisfies_comparator(v: Version, comp: str) -> bool:
    m = re.fullmatch(r"(\^|~|>=|<=|>|<|=)?\s*(v?[\dx*.]+)", comp)
    if not m:
        raise ValueError(f"unsupported comparator: {comp!r}")
    op, ver = m.group(1) or "", m.group(2)
    base, given = _partial(ver)
    if op == "^":
        if base[0] > 0:
            upper: Version = (base[0] + 1, 0, 0)
        elif base[1] > 0:
            upper = (0, base[1] + 1, 0)
        else:
            upper = (0, 0, base[2] + 1)
        return base <= v < upper
    if op == "~":
        upper = (base[0] + 1, 0, 0) if given == 1 else (base[0], base[1] + 1, 0)
        return base <= v < upper
    if op == ">=":
        return v >= base
    if op == ">":
        return v > base
    if op == "<=":
        return v <= base
    if op == "<":
        return v < base
    # bare or "=": partial versions behave like X-ranges
    if given == 1:
        return v[0] == base[0]
    if given == 2:
        return v[:2] == base[:2]
    return v == base


def satisfies(v: Version, rng: str) -> bool:
    for alt in rng.split("||"):
        alt = re.sub(r"(>=|<=|>|<|=|\^|~)\s+", r"\1", alt.strip())
        if not alt or alt == "*":
            return True
        hyphen = re.fullmatch(r"(\S+)\s+-\s+(\S+)", alt)
        if hyphen:
            if parse_version(hyphen.group(1)) <= v <= parse_version(hyphen.group(2)):
                return True
            continue
        if all(_satisfies_comparator(v, c) for c in alt.split()):
            return True
    return False


def floor_of(rng: str) -> Version:
    lows = []
    for alt in rng.split("||"):
        m = re.search(r"(?:\^|~|>=|=)?\s*v?(\d+(?:\.\d+){0,2})", alt)
        if not m:
            raise ValueError(f"cannot find lower bound in {alt!r}")
        lows.append(parse_version(m.group(1)))
    return min(lows)


def fmt(v: Version) -> str:
    return ".".join(map(str, v))


def check(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    nvmrc = (root / ".nvmrc").read_text(encoding="utf-8").strip()
    node_version_file = root / ".node-version"
    if not re.fullmatch(r"\d+\.\d+\.\d+", nvmrc):
        errors.append(f".nvmrc must be an exact X.Y.Z version, got {nvmrc!r}")
        return errors
    pinned = parse_version(nvmrc)
    if not node_version_file.is_file():
        errors.append(".node-version is missing")
    elif node_version_file.read_text(encoding="utf-8").strip() != nvmrc:
        errors.append(".node-version differs from .nvmrc")

    pkg = json.loads((root / "frontend/package.json").read_text(encoding="utf-8"))
    engines = pkg.get("engines", {}).get("node", "")
    if floor_of(engines) != pinned:
        errors.append(f"engines.node {engines!r} floor {fmt(floor_of(engines))} != .nvmrc {nvmrc}")

    lock = json.loads((root / "frontend/package-lock.json").read_text(encoding="utf-8"))
    for name, meta in sorted(lock.get("packages", {}).items()):
        eng = meta.get("engines")
        rng = eng.get("node") if isinstance(eng, dict) else None
        if not rng:
            continue
        try:
            ok = satisfies(pinned, rng)
        except ValueError as exc:
            errors.append(f"{name or '<root>'}: {exc}")
            continue
        if not ok:
            errors.append(f"{name or '<root>'}: engines.node {rng!r} rejects Node {nvmrc}")

    dc = json.loads((root / ".devcontainer/devcontainer.json").read_text(encoding="utf-8"))
    feature = dc.get("features", {}).get("ghcr.io/devcontainers/features/node:1", {})
    if str(feature.get("version")) != nvmrc:
        errors.append(f"devcontainer node feature version {feature.get('version')!r} != {nvmrc}")

    for wf in sorted((root / ".github/workflows").glob("*.y*ml")):
        text = wf.read_text(encoding="utf-8")
        for m in re.finditer(r"uses:\s*actions/setup-node@[^\n]*\n((?:\s+[^\n]*\n){0,6})", text):
            block = m.group(1)
            if "node-version-file: .nvmrc" not in block:
                rel = wf.relative_to(root)
                errors.append(f"{rel}: setup-node without node-version-file .nvmrc")
        if re.search(r"^\s*node-version:\s", text, re.M):
            errors.append(f"{wf.relative_to(root)}: literal node-version (use .nvmrc)")

    stale = re.compile(r"(?:Node(?:\.js)?|need)\s+(\d+\.\d+(?:\.\d+)?)\+")
    for rel in _STALE_DOC_FILES:
        path = root / rel
        if not path.is_file():
            continue
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for m in stale.finditer(line):
                if m.group(1) != nvmrc:
                    errors.append(f"{rel}:{lineno}: advertises Node {m.group(1)}+ (want {nvmrc}+)")
    return errors


def main() -> int:
    errors = check()
    for e in errors:
        print(f"ERROR: {e}", file=sys.stderr)
    if errors:
        return 1
    print("node version consistency OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
