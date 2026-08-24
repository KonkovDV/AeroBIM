"""Official published IDS profile manifest — fail-closed parsing and honesty locks.

A profile bundles byte-exact references to authority-published IDS 1.0 files
(SPb GAU CGE at spbexp.ru/bim/docs/). The manifest never rewrites, translates,
or interpolates requirements: it pins path + SHA-256 + IDS schema version per
file, verbatim. A manifest that does not parse, lists a file that is missing
or hash-mismatched, declares an IDS schema version other than 1.0, or carries
a customer-signature / RT-closure flag raises :class:`OfficialIdsProfileError`.
Silence is never success.

Domain-pure: no IO, no xmlschema/IfcTester imports. IO and XSD/model gates
live in ``aerobim.tools.validate_spb_cge_profile``.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, NoReturn

ARTIFACT_TYPE = "official_ids_profile_manifest"
SUPPORTED_MANIFEST_SCHEMA_VERSION = "1.0.0"
SUPPORTED_IDS_SCHEMA_VERSION = "1.0"
IDS_NAMESPACE_1_0 = "http://standards.buildingsmart.org/IDS"
PROVENANCE_STATUSES = frozenset({"OFFICIAL_PUBLISHED", "DERIVED_UNOFFICIAL"})

_PROFILE_ID_RE = re.compile(r"^[A-Z0-9][A-Z0-9-]*$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_HONESTY_FALSE_FIELDS = (
    "signed_by_customer",
    "closes_rt001",
    "closes_rt002",
    "closes_rt003",
    "samolet_alias",
)


class OfficialIdsProfileError(ValueError):
    """Fail-closed profile rejection. Any raise here must fail the run."""


@dataclass(frozen=True)
class ProfileFileEntry:
    path: str
    subject: str
    title: str
    sha256: str
    size_bytes: int
    ids_schema_version: str
    doc_edition: str


@dataclass(frozen=True)
class ProfileEdition:
    subject: str
    edition: str
    edition_date: str


@dataclass(frozen=True)
class OfficialIdsProfile:
    profile_id: str
    human_name: str
    language: str
    provenance_status: str
    organization: str
    source_page: str
    retrieval_date: str
    editions: tuple[ProfileEdition, ...]
    pack_root: str
    files: tuple[ProfileFileEntry, ...]
    scope_applies_to: tuple[str, ...]
    scope_not_applies_to: tuple[str, ...]
    coverage_checks: tuple[str, ...]
    coverage_does_not_check: tuple[str, ...]
    disclaimer: str
    payload: dict[str, Any]

    @property
    def subjects(self) -> frozenset[str]:
        return frozenset(entry.subject for entry in self.files)


def _fail(field: str, detail: str) -> NoReturn:
    raise OfficialIdsProfileError(f"profile manifest {field}: {detail}")


def _require_str(payload: dict[str, Any], field: str, *, where: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        _fail(f"{where}.{field}", "missing or empty string")
    return str(value).strip()


def _require_str_list(payload: dict[str, Any], field: str, *, where: str) -> tuple[str, ...]:
    value = payload.get(field)
    if not isinstance(value, list) or not value:
        _fail(f"{where}.{field}", "missing or empty list")
    items: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            _fail(f"{where}.{field}", "entries must be non-empty strings")
        items.append(item.strip())
    return tuple(items)


def _parse_file_entry(raw: Any, *, index: int) -> ProfileFileEntry:
    where = f"files[{index}]"
    if not isinstance(raw, dict):
        _fail(where, "entry must be an object")
    path = _require_str(raw, "path", where=where)
    if "\\" in path or path.startswith("/") or ".." in path.split("/"):
        _fail(f"{where}.path", f"must be a POSIX relative path inside the pack root: {path!r}")
    if not path.lower().endswith(".ids"):
        _fail(f"{where}.path", f"not an .ids file: {path!r}")
    sha256 = _require_str(raw, "sha256", where=where).lower()
    if not _SHA256_RE.match(sha256):
        _fail(f"{where}.sha256", f"not 64 lowercase hex chars: {sha256!r}")
    size_bytes = raw.get("size_bytes")
    if not isinstance(size_bytes, int) or isinstance(size_bytes, bool) or size_bytes <= 0:
        _fail(f"{where}.size_bytes", "must be a positive integer")
    ids_schema_version = _require_str(raw, "ids_schema_version", where=where)
    if ids_schema_version != SUPPORTED_IDS_SCHEMA_VERSION:
        _fail(
            f"{where}.ids_schema_version",
            f"declared {ids_schema_version!r}; only IDS "
            f"{SUPPORTED_IDS_SCHEMA_VERSION} (buildingSMART) is accepted — refusing "
            "to convert or reinterpret another schema",
        )
    return ProfileFileEntry(
        path=path,
        subject=_require_str(raw, "subject", where=where),
        title=_require_str(raw, "title", where=where),
        sha256=sha256,
        size_bytes=int(size_bytes),
        ids_schema_version=ids_schema_version,
        doc_edition=_require_str(raw, "doc_edition", where=where),
    )


def parse_official_ids_profile(payload: Any) -> OfficialIdsProfile:
    """Parse and validate a profile manifest dict. Fail-closed on any defect."""
    if not isinstance(payload, dict):
        _fail("", "manifest is not a JSON object")

    schema_version = _require_str(payload, "schema_version", where="manifest")
    if schema_version != SUPPORTED_MANIFEST_SCHEMA_VERSION:
        _fail(
            "schema_version",
            f"declared {schema_version!r}; supported is {SUPPORTED_MANIFEST_SCHEMA_VERSION!r}",
        )
    artifact_type = _require_str(payload, "artifact_type", where="manifest")
    if artifact_type != ARTIFACT_TYPE:
        _fail("artifact_type", f"declared {artifact_type!r}; expected {ARTIFACT_TYPE!r}")

    profile_id = _require_str(payload, "profile_id", where="manifest")
    if not _PROFILE_ID_RE.match(profile_id):
        _fail("profile_id", f"must be UPPER-DASH form: {profile_id!r}")

    provenance_status = _require_str(payload, "provenance_status", where="manifest")
    if provenance_status not in PROVENANCE_STATUSES:
        _fail(
            "provenance_status",
            f"{provenance_status!r} not in {sorted(PROVENANCE_STATUSES)}; derived rules "
            "must be marked DERIVED_UNOFFICIAL, never passed off as official",
        )

    for field in _HONESTY_FALSE_FIELDS:
        if payload.get(field) is not False:
            _fail(
                field,
                f"must be JSON false (got {payload.get(field)!r}); profile never "
                "closes RT-001/RT-002/RT-003 and is never customer-signed",
            )
    if (
        not isinstance(payload.get("signed_by_customer_reason"), str)
        or not str(payload.get("signed_by_customer_reason")).strip()
    ):
        _fail("signed_by_customer_reason", "missing or empty string")

    origin = payload.get("origin")
    if not isinstance(origin, dict):
        _fail("origin", "missing or not an object")
    organization = _require_str(origin, "organization", where="origin")
    source_page = _require_str(origin, "source_page", where="origin")
    if not source_page.startswith("https://"):
        _fail("origin.source_page", f"must be an https URL: {source_page!r}")
    retrieval_date = _require_str(origin, "retrieval_date", where="origin")
    if not _DATE_RE.match(retrieval_date):
        _fail("origin.retrieval_date", f"must be YYYY-MM-DD: {retrieval_date!r}")

    raw_editions = origin.get("editions")
    if not isinstance(raw_editions, list) or not raw_editions:
        _fail("origin.editions", "missing or empty list")
    editions: list[ProfileEdition] = []
    for index, raw_edition in enumerate(raw_editions):
        where = f"origin.editions[{index}]"
        if not isinstance(raw_edition, dict):
            _fail(where, "entry must be an object")
        edition_date = _require_str(raw_edition, "edition_date", where=where)
        if not _DATE_RE.match(edition_date):
            _fail(f"{where}.edition_date", f"must be YYYY-MM-DD: {edition_date!r}")
        editions.append(
            ProfileEdition(
                subject=_require_str(raw_edition, "subject", where=where),
                edition=_require_str(raw_edition, "edition", where=where),
                edition_date=edition_date,
            )
        )

    scope = payload.get("scope")
    if not isinstance(scope, dict):
        _fail("scope", "missing or not an object")
    applies_to = _require_str_list(scope, "applies_to", where="scope")
    not_applies_to = _require_str_list(scope, "not_applies_to", where="scope")

    coverage = payload.get("coverage")
    if not isinstance(coverage, dict):
        _fail("coverage", "missing or not an object")
    checks = _require_str_list(coverage, "checks", where="coverage")
    does_not_check = _require_str_list(coverage, "does_not_check", where="coverage")

    raw_files = payload.get("files")
    if not isinstance(raw_files, list) or not raw_files:
        _fail("files", "missing or empty list")
    files = tuple(_parse_file_entry(raw, index=i) for i, raw in enumerate(raw_files))

    seen: set[str] = set()
    for entry in files:
        if entry.path in seen:
            _fail("files", f"duplicate path: {entry.path!r}")
        seen.add(entry.path)

    edition_subjects = {edition.subject for edition in editions}
    file_subjects = {entry.subject for entry in files}
    undeclared = file_subjects - edition_subjects
    if undeclared:
        _fail(
            "files",
            f"subjects without a declared origin edition: {sorted(undeclared)}; "
            "subjects (e.g. OKS vs RII) must not be mixed under one edition",
        )

    disclaimer = _require_str(payload, "disclaimer", where="manifest")
    pack_root = _require_str(payload, "pack_root", where="manifest")
    if (
        pack_root.startswith("/")
        or "\\" in pack_root
        or ".." in pack_root.split("/")
        or (len(pack_root) >= 2 and pack_root[1] == ":")
    ):
        _fail("pack_root", f"must be a repo-relative POSIX path: {pack_root!r}")

    return OfficialIdsProfile(
        profile_id=profile_id,
        human_name=_require_str(payload, "human_name", where="manifest"),
        language=_require_str(payload, "language", where="manifest"),
        provenance_status=provenance_status,
        organization=organization,
        source_page=source_page,
        retrieval_date=retrieval_date,
        editions=tuple(editions),
        pack_root=pack_root,
        files=files,
        scope_applies_to=applies_to,
        scope_not_applies_to=not_applies_to,
        coverage_checks=checks,
        coverage_does_not_check=does_not_check,
        disclaimer=disclaimer,
        payload=dict(payload),
    )


def find_file_mismatches(
    profile: OfficialIdsProfile,
    actual: dict[str, tuple[str, int] | None],
) -> tuple[str, ...]:
    """Compare declared files against observed ``(sha256, size)`` (None = missing)."""
    problems: list[str] = []
    for entry in profile.files:
        observed = actual.get(entry.path)
        if observed is None:
            problems.append(f"{entry.path}: file missing")
            continue
        digest, size = observed
        if digest.lower() != entry.sha256:
            problems.append(
                f"{entry.path}: sha256 mismatch (manifest {entry.sha256[:12]}…, "
                f"actual {digest.lower()[:12]}…)"
            )
        if size != entry.size_bytes:
            problems.append(
                f"{entry.path}: size_bytes mismatch (manifest {entry.size_bytes}, actual {size})"
            )
    extra = sorted(set(actual) - {entry.path for entry in profile.files})
    for path in extra:
        problems.append(f"{path}: file on disk is not declared in the manifest")
    return tuple(problems)


def canonical_profile_hash(profile: OfficialIdsProfile) -> str:
    """SHA-256 over canonical JSON of the manifest payload (artifact identity)."""
    canonical = json.dumps(
        profile.payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
