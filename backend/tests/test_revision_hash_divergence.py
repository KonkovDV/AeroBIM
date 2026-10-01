"""TR-242 guard (Red Team A6): same document + same/absent revision but divergent
content hash is not a silent merge -- it surfaces for HITL."""

from __future__ import annotations

from aerobim.domain.ingestion import detect_revision_merge_conflicts, stamp_requirement_source
from aerobim.domain.models import ConflictKind, RequirementSource, Severity, SourceKind


def _src(kind: SourceKind, *, sha256: str, revision: str | None = None) -> RequirementSource:
    return stamp_requirement_source(
        RequirementSource(text="x", source_kind=kind),
        source_id="PKG-1",
        doc_type="specification",
        revision=revision,
        sha256=sha256,
    )


def test_same_revision_divergent_hash_warns() -> None:
    sources = [
        _src(SourceKind.STRUCTURED_TEXT, sha256="aaa", revision="A"),
        _src(SourceKind.TECHNICAL_SPECIFICATION, sha256="bbb", revision="A"),
    ]
    issues = detect_revision_merge_conflicts(sources)
    assert len(issues) == 1
    assert issues[0].rule_id == "AEROBIM-REVISION-HASH"
    assert issues[0].severity is Severity.WARNING
    assert issues[0].conflict_kind is ConflictKind.AMBIGUOUS_MAPPING


def test_missing_revision_divergent_hash_warns() -> None:
    sources = [
        _src(SourceKind.STRUCTURED_TEXT, sha256="aaa"),
        _src(SourceKind.TECHNICAL_SPECIFICATION, sha256="bbb"),
    ]
    assert [issue.rule_id for issue in detect_revision_merge_conflicts(sources)] == [
        "AEROBIM-REVISION-HASH"
    ]


def test_identical_hash_is_true_duplicate_not_conflict() -> None:
    sources = [
        _src(SourceKind.STRUCTURED_TEXT, sha256="same", revision="A"),
        _src(SourceKind.TECHNICAL_SPECIFICATION, sha256="same", revision="A"),
    ]
    assert detect_revision_merge_conflicts(sources) == []


def test_missing_hashes_do_not_fabricate_conflict() -> None:
    # No sha256 on either side -> cannot compare content -> no fabricated conflict.
    sources = [
        RequirementSource(
            text="a",
            source_kind=SourceKind.STRUCTURED_TEXT,
            source_id="PKG-1",
            doc_type="specification",
            revision="A",
        ),
        RequirementSource(
            text="b",
            source_kind=SourceKind.TECHNICAL_SPECIFICATION,
            source_id="PKG-1",
            doc_type="specification",
            revision="A",
        ),
    ]
    assert detect_revision_merge_conflicts(sources) == []


def test_different_revision_still_errors_not_downgraded() -> None:
    sources = [
        _src(SourceKind.STRUCTURED_TEXT, sha256="aaa", revision="A"),
        _src(SourceKind.TECHNICAL_SPECIFICATION, sha256="bbb", revision="B"),
    ]
    issues = detect_revision_merge_conflicts(sources)
    assert len(issues) == 1
    assert issues[0].rule_id == "AEROBIM-REVISION-MERGE"
    assert issues[0].severity is Severity.ERROR
