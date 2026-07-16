"""Advisory use case: compile requirements → IDS draft (never sets summary.passed)."""

from __future__ import annotations

from aerobim.domain.models import RequirementSource
from aerobim.domain.norm_assist import IdsCompileDraft, NormPassage
from aerobim.domain.ports import NormCorpusRetriever, RequirementToIdsCompiler


class CompileRequirementsToIdsUseCase:
    def __init__(
        self,
        compiler: RequirementToIdsCompiler,
        norm_retriever: NormCorpusRetriever | None = None,
    ) -> None:
        self._compiler = compiler
        self._norm_retriever = norm_retriever

    def execute(
        self,
        source: RequirementSource,
        *,
        enrich_query: str | None = None,
    ) -> tuple[IdsCompileDraft, tuple[NormPassage, ...]]:
        draft = self._compiler.compile(source)
        passages: tuple[NormPassage, ...] = ()
        if self._norm_retriever is not None and enrich_query:
            passages = tuple(self._norm_retriever.retrieve(enrich_query, top_k=5))
        return draft, passages
