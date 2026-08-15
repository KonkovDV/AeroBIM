from __future__ import annotations

from aerobim.core.config.settings import Settings
from aerobim.core.di.container import Container, Lifecycle
from aerobim.core.di.tokens import Tokens
from aerobim.domain.models import ToleranceConfig
from aerobim.infrastructure.adapters.docling_office_document_ingestor import (
    OfficeDocumentIngestor,
)
from aerobim.infrastructure.adapters.docling_requirement_extractor import (
    StructuredRequirementExtractor,
)
from aerobim.infrastructure.adapters.ezdxf_cad_entity_loader import EzdxfCadEntityLoader
from aerobim.infrastructure.adapters.ezdxf_cad_model_ingestor import EzdxfCadModelIngestor
from aerobim.infrastructure.adapters.heuristic_layout_region_detector import (
    HeuristicLayoutRegionDetector,
)
from aerobim.infrastructure.adapters.ifc_space_inventory import (
    IfcOpenShellSpaceInventoryExtractor,
)
from aerobim.infrastructure.adapters.narrative_rule_synthesizer import NarrativeRuleSynthesizer
from aerobim.infrastructure.adapters.ocr_fallback_multimodal_drawing_pipeline import (
    OcrFallbackMultimodalDrawingPipeline,
)
from aerobim.infrastructure.adapters.oda_cad_model_ingestor import OdaCadModelIngestor
from aerobim.infrastructure.adapters.raster_drawing_analyzer import RasterDrawingAnalyzer
from aerobim.infrastructure.adapters.structured_drawing_analyzer import StructuredDrawingAnalyzer
from aerobim.infrastructure.di._di_factories import (
    _build_drawing_analyzer_port,
    _build_extraction_integrity_producer,
)


def register_group(
    container: Container,
    runtime_settings: Settings,
    *,
    tolerance: ToleranceConfig,
) -> None:
    container.register(
        Tokens.REQUIREMENT_EXTRACTOR,
        lambda _container: StructuredRequirementExtractor(),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.NARRATIVE_RULE_SYNTHESIZER,
        lambda _container: NarrativeRuleSynthesizer(),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.DRAWING_ANALYZER,
        lambda _container: StructuredDrawingAnalyzer(),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.RASTER_DRAWING_ANALYZER,
        lambda _container: RasterDrawingAnalyzer(),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.EXTRACTION_INTEGRITY_PRODUCER,
        lambda current: _build_extraction_integrity_producer(current),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.CAD_MODEL_INGESTOR,
        lambda _container: EzdxfCadModelIngestor(),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.OFFICE_DOCUMENT_INGESTOR,
        lambda _container: OfficeDocumentIngestor(),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.DRAWING_REGION_DETECTOR,
        lambda _container: HeuristicLayoutRegionDetector(),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.MULTIMODAL_DRAWING_PIPELINE,
        lambda current: OcrFallbackMultimodalDrawingPipeline(
            raster_analyzer=current.resolve(Tokens.RASTER_DRAWING_ANALYZER),
            region_detector=current.resolve(Tokens.DRAWING_REGION_DETECTOR),
        ),
        lifecycle=Lifecycle.SINGLETON,
    )
    # Advisory VLM (§3/§7): available under vlm_advisory_ready(), but DELIBERATELY
    # NOT consumed by AnalyzeProjectPackageUseCase — its candidate regions must
    # never reach engine_issues / summary.passed (advisory OFF==ON invariant).
    container.register(
        Tokens.IFC_SPACE_INVENTORY,
        lambda _current: IfcOpenShellSpaceInventoryExtractor(),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.ODA_CAD_MODEL_INGESTOR,
        lambda current: OdaCadModelIngestor(
            enabled=current.resolve(Tokens.SETTINGS).oda_cad_enabled
        ),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.CAD_ENTITY_LOADER,
        lambda _container: EzdxfCadEntityLoader(),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.DRAWING_ANALYZER_PORT,
        lambda current: _build_drawing_analyzer_port(current),
        lifecycle=Lifecycle.SINGLETON,
    )
