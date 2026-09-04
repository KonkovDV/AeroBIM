
"""Measurement vs residual volumes for RT-001 / RT-002 / RT-003.

Owner re-scope 2026-09-04: what Samolet did not hand over is replaced by
public / synthetic proxies for *measurement*. Channel-pack carriers already
pinned in ``deep_study_facts`` (EIR v4 + BIM-standard v4 as text; three NWD
federations) close those measurement volumes. They are not a signed IDS and
not an IfcSystem MEP graph. Undifferentiated ``closes_rt001`` /
``closes_rt002`` / ``closes_rt003`` stay false. ``PrecisionClaim.publishable``
stays customer-gated. MEP delivered is not claimed. Checkpoint is ``GO``
(regulatory-measurement MVP). ``customer_go`` stays false until dual human
raters, a named appointing-party signed IDS, system MEP, and CDE T2.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Final

from aerobim.domain import rt001_dual_rater_simulation as dual_rater
from aerobim.domain.checkpoint import CHECKPOINT, CUSTOMER_GO, GO_KIND
from aerobim.domain.deep_study_facts import deep_study_snapshot
from aerobim.domain.tz_proxy_constructs import typical_remark_taxonomy_proxy

VOLUME_RE_SCOPE_DATE: Final = "2026-09-04"
SCHEMA_VERSION: Final = "1.5.0"
# Speech letters (jury): RT-001b := humans (OPEN). Never utter «RT-001b CLOSED».
# Machine b-keys are not a single letter. b1/b2/b3 are the unambiguous ids.
CLAIM_LEVEL: Final = "measurement_proxy_not_customer"

PLANTED_CLASH_REL: Final = "docs/evidence/federated-clash-planted-2026-08.json"
MEP_INVENTORY_REL: Final = "docs/evidence/federated-mep-inventory-2026-08.json"
HVAC_IFC_REL: Final = "samples/mep/hvac-sprinkler-systems.ifc"
AGR_PACK_REL: Final = "samples/norm-packs/moscow_agr_2026/pack.json"
FREEZE_REL: Final = "samples/benchmarks/rt001-preregistration-synthetic-freeze-2026-08-14.json"
EXP_B_REL: Final = "docs/evidence/EXPERIMENT_B_TYPICAL_REMARKS_KR_COVERAGE_2026_08.md"
DEMO_REL: Final = "samples/demo/vertical-slice-2026-08-11/manifest.json"
MOEXP_POINTER_REL: Final = "samples/ids/moexp/jurisdiction-profile-pointer.json"
SPB_MANIFEST_REL: Final = "samples/profiles/spb-cge/manifest.json"
MOEXP_IDS_REL: Final = "samples/ids/moexp/pack"
SPB_IDS_REL: Final = "samples/ids/spbexp/pack"
AGR_IDS_REL: Final = "samples/ids/moscow-agr/pack"
SYNTHETIC_LABELS_REL: Final = "samples/benchmarks/detection-precision/labels-synthetic.json"
PLANTED_IFC_RELS: Final = (
    "samples/ifc/clash-federated-box-a.ifc",
    "samples/ifc/clash-federated-box-b.ifc",
    "samples/ifc/clash-federated-pipe-b.ifc",
)
MIN_MOEXP_IDS: Final = 20
MIN_SPB_IDS: Final = 15
MIN_AGR_IDS: Final = 3

CLAIM_BOUNDARY: Final = (
    "Measurement volumes use public IDS, RF typical-error catalogs, fixture "
    "gold, planted IfcClash, a two-pass protocol rehearsal, and git-safe "
    "channel-pack carriers (EIR v4 + BIM-standard v4 as text; three NWD "
    "federations), and an in-repo IfcSystem graph rehearsal (HVAC fixture). "
    "That is not product accuracy, not two human raters, not a Samolet "
    "signature, not mep_system_clash=OK, not CDE import. "
    "closes_rt001/002/003 stay false. Checkpoint GO "
    "(regulatory_measurement_mvp; customer_go false)."
)


class RtBlockerVolumeError(ValueError):
    """Substitute inventory is missing or an undifferentiated close leaked."""


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RtBlockerVolumeError(f"expected JSON object in {path}")
    return data


def _count_ids(directory: Path) -> int:
    if not directory.is_dir():
        return 0
    return sum(1 for path in directory.rglob("*.ids") if path.is_file())


def _spb_manifest_honest(manifest: Mapping[str, Any]) -> bool:
    return (
        manifest.get("provenance_status") == "OFFICIAL_PUBLISHED"
        and manifest.get("signed_by_customer") is False
        and manifest.get("samolet_alias") is False
        and manifest.get("closes_rt002") is False
    )


def _planted_geometric_closed(planted: Mapping[str, Any]) -> bool:
    if planted.get("mep_system_clash") != "NOT_VERIFIED":
        return False
    if planted.get("closes_rt003") is True:
        return False
    runs = planted.get("runs")
    if not isinstance(runs, list) or len(runs) < 2:
        return False
    needed = {
        "planted_federated_crossing_walls",
        "planted_federated_pipe_vs_wall",
    }
    seen: set[str] = set()
    for row in runs:
        if not isinstance(row, dict):
            return False
        label = str(row.get("label") or "")
        if label not in needed:
            continue
        if row.get("status") != "RUN":
            return False
        if int(row.get("clash_count") or 0) < 1:
            return False
        if row.get("mep_system_clash") != "NOT_VERIFIED":
            return False
        seen.add(label)
    return seen == needed


def _channel_eir_carrier_closed(study: Mapping[str, Any]) -> bool:
    """Appointing-party EIR as a document on the channel pack, not a signed IDS."""

    return (
        study.get("eir_v4_present") is True
        and study.get("bim_standard_v4_present") is True
        and study.get("customer_approved_ids") is False
        and study.get("names_in_git") is False
        and study.get("hashes_in_git") is False
        and study.get("closes_rt002") is not True
    )


def _channel_navis_carrier_closed(study: Mapping[str, Any]) -> bool:
    """Federated coordination as NWD on the channel pack, not an IFC system graph."""

    return (
        int(study.get("nwd_federation_count") or 0) >= 3
        and study.get("parse_rvt_nwd_lira") is False
        and study.get("names_in_git") is False
        and study.get("hashes_in_git") is False
        and study.get("closes_rt003") is not True
    )


def _ifc_system_graph_rehearsal_closed(
    inventory: Mapping[str, Any], repo: Path
) -> bool:
    """IfcSystem + RelAssignsToGroup on the HVAC fixture — not pipe-vs-wall geometry."""

    if inventory.get("mep_system_clash") != "NOT_VERIFIED":
        return False
    if inventory.get("closes_rt003") is True:
        return False
    if not (repo / HVAC_IFC_REL).is_file():
        return False
    rows = inventory.get("rows")
    if not isinstance(rows, list):
        return False
    fixture = next(
        (row for row in rows if isinstance(row, dict) and row.get("label") == "eng_fixture"),
        None,
    )
    if not isinstance(fixture, dict) or fixture.get("status") != "RUN":
        return False
    counts = fixture.get("counts") if isinstance(fixture.get("counts"), dict) else {}
    if int(counts.get("IfcSystem") or 0) < 2:
        return False
    geometry = inventory.get("geometry") if isinstance(inventory.get("geometry"), dict) else {}
    hvac = geometry.get("hvac_fixture_graph_aabb") if isinstance(geometry, dict) else None
    if not isinstance(hvac, dict):
        return False
    if hvac.get("status") != "RUN":
        return False
    if int(hvac.get("nodes") or 0) < 2:
        return False
    if hvac.get("geometry_verified") is True:
        return False
    if hvac.get("synthetic") is not True:
        return False
    return True


def _alias_split_ids(rt001: dict[str, Any], rt003: dict[str, Any]) -> None:
    """Unambiguous b1/b2/b3 keys; legacy b_* keys stay for consumers."""

    rt001["b1_protocol_rehearsal"] = rt001["b_protocol_rehearsal"]
    rt001["b2_criterion_dual_rater"] = rt001["b_criterion_dual_rater"]
    rt003["b1_navis_federation_carrier"] = rt003["b_navis_federation_carrier"]
    rt003["b2_ifc_system_graph_rehearsal"] = rt003["b_ifc_system_graph_rehearsal"]
    rt003["b3_mep_system_clash"] = rt003["b_mep_system_clash"]


def assemble_rt_blocker_volumes(repo: Path) -> dict[str, Any]:
    """Compose the a/b volume snapshot from committed substitute evidence."""

    planted = _load_json(repo / PLANTED_CLASH_REL)
    inventory = _load_json(repo / MEP_INVENTORY_REL)
    agr = _load_json(repo / AGR_PACK_REL)
    freeze = _load_json(repo / FREEZE_REL)
    pointer = _load_json(repo / MOEXP_POINTER_REL)
    spb = _load_json(repo / SPB_MANIFEST_REL)
    taxonomy = typical_remark_taxonomy_proxy()
    catalogs = {
        str(row.get("id")): row for row in taxonomy.get("catalogs") or [] if isinstance(row, dict)
    }
    kirov = catalogs.get("kirov-kr") or {}
    planted_ifc_ok = all((repo / rel).is_file() for rel in PLANTED_IFC_RELS)
    geometric = _planted_geometric_closed(planted) and planted_ifc_ok
    agr_approved = agr.get("status") == "approved" and isinstance(agr.get("approval"), dict)
    raters = freeze.get("raters") if isinstance(freeze.get("raters"), dict) else {}
    human_raters = int(raters.get("independent_human_raters") or 0)
    moexp_ids = _count_ids(repo / MOEXP_IDS_REL)
    spb_ids = _count_ids(repo / SPB_IDS_REL)
    agr_ids = _count_ids(repo / AGR_IDS_REL)
    regulatory = (
        agr_approved
        and _spb_manifest_honest(spb)
        and pointer.get("samolet_alias") is not True
        and pointer.get("closes_rt002") is not True
        and moexp_ids >= MIN_MOEXP_IDS
        and spb_ids >= MIN_SPB_IDS
        and agr_ids >= MIN_AGR_IDS
    )
    content_pairing = (
        int(kirov.get("detectable") or 0) >= 4
        and freeze.get("corpus_kind") == "synthetic"
        and freeze.get("closes_rt001") is not True
        and human_raters == 0
        and (repo / EXP_B_REL).is_file()
        and (repo / DEMO_REL).is_file()
        and (repo / SYNTHETIC_LABELS_REL).is_file()
    )

    sim = dual_rater.assemble_rt001_dual_rater_simulation(repo)
    study = deep_study_snapshot()
    eir_carrier = _channel_eir_carrier_closed(study)
    navis_carrier = _channel_navis_carrier_closed(study)
    system_graph = _ifc_system_graph_rehearsal_closed(inventory, repo)

    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "artifact_type": "rt_blocker_volumes",
        "claim_level": CLAIM_LEVEL,
        "claim_boundary": CLAIM_BOUNDARY,
        "volume_re_scope_date": VOLUME_RE_SCOPE_DATE,
        "checkpoint": CHECKPOINT,
        "go_kind": GO_KIND,
        "customer_go": CUSTOMER_GO,
        "market_go": False,
        "deployment_go": False,
        "closes_rt001": False,
        "closes_rt002": False,
        "closes_rt003": False,
        "precision_claim_publishable": False,
        "mep_delivered": False,
        "RT-001": {
            "a_content_pairing": "CLOSED" if content_pairing else "OPEN",
            "b_protocol_rehearsal": sim["b_protocol_rehearsal"],
            "b_criterion_dual_rater": "OPEN",
            "c_customer_corpus": "OPEN",
            "undifferentiated_closed_forbidden": True,
            "open_benches_are_different_contour": True,
            "substitute": (
                "RF expertise typical-error catalogs (Experiment B) + public "
                "examination IDS + fixture/injection gold + two simulated "
                "independent passes with live κ/α/AC1. Not two humans."
            ),
            "kirov_kr_detectable": kirov.get("detectable"),
            "independent_human_raters": human_raters,
            "dual_rater_n": sim["n"],
            "dual_rater_kappa": sim["cohens_kappa"],
            "dual_rater_alpha": sim["krippendorff_alpha"],
            "dual_rater_ac1": sim["gwet_ac1"],
        },
        "RT-002": {
            "a_regulatory": "CLOSED" if regulatory else "OPEN",
            "b_eir_carrier": "CLOSED" if eir_carrier else "OPEN",
            "b_corporate": "OPEN",
            "c_corporate_signed": "OPEN",
            "undifferentiated_closed_forbidden": True,
            "substitute": (
                "City/MOEXP/CGE published IDS as the measurement ruler "
                "(RT-002a). Channel-pack EIR v4.0 + BIM-standard v4.0 as text "
                "(RT-002b carrier). Public examination IDS is not the "
                "appointing-party EIR. Text EIR is not a signed IDS."
            ),
            "agr_pack_status": agr.get("status"),
            "pointer_samolet_alias": bool(pointer.get("samolet_alias")),
            "eir_v4_present": bool(study.get("eir_v4_present")),
            "bim_standard_v4_present": bool(study.get("bim_standard_v4_present")),
            "eir_lod_mep_disciplines_named": bool(
                study.get("eir_lod_mep_disciplines_named")
            ),
            "customer_approved_ids": bool(study.get("customer_approved_ids")),
            "ids_counts": {
                "moexp": moexp_ids,
                "spb_cge": spb_ids,
                "moscow_agr": agr_ids,
            },
        },
        "RT-003": {
            "a_federated_geometric_rehearsal": "CLOSED" if geometric else "OPEN",
            "b_navis_federation_carrier": "CLOSED" if navis_carrier else "OPEN",
            "b_ifc_system_graph_rehearsal": "CLOSED" if system_graph else "OPEN",
            "b_mep_system_clash": "OPEN",
            "c_customer_federated_ifc": "OPEN",
            "undifferentiated_closed_forbidden": True,
            "substitute": (
                "In-repo planted IfcClash is geometric rehearsal (RT-003a). "
                "HVAC fixture IfcSystem graph (2 systems, RelAssignsToGroup) "
                "is RT-003b rehearsal — not pipe-vs-wall. Channel pack has "
                "three NWD federations; native unread. Zero duct/pipe/cable "
                "on customer IFC. EIR names OV/VK/ITP/EOM/SS LOD; models absent."
            ),
            "mep_system_clash": planted.get("mep_system_clash"),
            "nwd_federation_count": int(study.get("nwd_federation_count") or 0),
            "mep_duct_pipe_cable_count": int(study.get("mep_duct_pipe_cable_count") or 0),
            "flow_terminal_present_on_ar": bool(study.get("flow_terminal_present_on_ar")),
            "eir_lod_mep_disciplines_named": bool(
                study.get("eir_lod_mep_disciplines_named")
            ),
            "hvac_ifc_system_count": 2,
            "parse_rvt_nwd_lira": bool(study.get("parse_rvt_nwd_lira")),
            "planted_pin": PLANTED_CLASH_REL,
            "mep_inventory_pin": MEP_INVENTORY_REL,
        },
        "evidence_present": {
            "experiment_b": (repo / EXP_B_REL).is_file(),
            "demo_manifest": (repo / DEMO_REL).is_file(),
            "planted_clash": (repo / PLANTED_CLASH_REL).is_file(),
            "planted_ifc": planted_ifc_ok,
            "agr_pack": (repo / AGR_PACK_REL).is_file(),
            "label_freeze": (repo / FREEZE_REL).is_file(),
            "synthetic_labels": (repo / SYNTHETIC_LABELS_REL).is_file(),
            "spb_cge_manifest": (repo / SPB_MANIFEST_REL).is_file(),
            "moexp_ids": moexp_ids >= MIN_MOEXP_IDS,
            "spb_ids": spb_ids >= MIN_SPB_IDS,
            "agr_ids": agr_ids >= MIN_AGR_IDS,
            "dual_rater_csv": (repo / dual_rater.CSV_REL).is_file(),
            "dual_rater_md": (repo / dual_rater.EVIDENCE_MD_REL).is_file(),
            "channel_eir_v4": bool(study.get("eir_v4_present")),
            "channel_bim_standard_v4": bool(study.get("bim_standard_v4_present")),
            "channel_nwd_federations": int(study.get("nwd_federation_count") or 0) >= 3,
            "hvac_ifc_system_fixture": (repo / HVAC_IFC_REL).is_file(),
            "mep_inventory_pin": (repo / MEP_INVENTORY_REL).is_file(),
        },
        "volume_speech_map": {
            "RT-001a": "a_content_pairing",
            "RT-001b": "b2_criterion_dual_rater",
            "RT-001c": "c_customer_corpus",
            "RT-002a": "a_regulatory",
            "RT-002b": "b_eir_carrier",
            "RT-002c": "c_corporate_signed",
            "RT-003a": "a_federated_geometric_rehearsal",
            "RT-003b": "b2_ifc_system_graph_rehearsal",
            "RT-003c": "b3_mep_system_clash",
        },
        "undifferentiated_letter_closed_forbidden": (
            "RT-001 CLOSED",
            "RT-002 CLOSED",
            "RT-003 CLOSED",
            "RT-001b CLOSED",
            "RT-003c CLOSED",
        ),
    }
    _alias_split_ids(payload["RT-001"], payload["RT-003"])
    require_honest_rt_blocker_volumes(payload)
    return payload


def require_honest_rt_blocker_volumes(payload: Mapping[str, Any]) -> None:
    errors: list[str] = []
    if payload.get("checkpoint") != CHECKPOINT:
        errors.append(f"checkpoint={payload.get('checkpoint')!r}")
    if payload.get("go_kind") != GO_KIND:
        errors.append(f"go_kind={payload.get('go_kind')!r}")
    if payload.get("customer_go") is not False:
        errors.append("customer_go must stay false")
    for key in ("closes_rt001", "closes_rt002", "closes_rt003"):
        if payload.get(key) is not False:
            errors.append(f"{key} must stay false")
    if payload.get("precision_claim_publishable") is not False:
        errors.append("precision_claim_publishable must stay false")
    if payload.get("mep_delivered") is not False:
        errors.append("mep_delivered must stay false")
    rt001 = payload.get("RT-001")
    rt002 = payload.get("RT-002")
    rt003 = payload.get("RT-003")
    if not isinstance(rt001, dict) or rt001.get("a_content_pairing") != "CLOSED":
        errors.append("RT-001a content pairing must be CLOSED on substitutes")
    if isinstance(rt001, dict) and rt001.get("open_benches_are_different_contour") is not True:
        errors.append("open benches must stay a different contour from RT-001b")
    if not isinstance(rt001, dict) or rt001.get("b_criterion_dual_rater") != "OPEN":
        errors.append("RT-001b dual-rater must stay OPEN")
    if not isinstance(rt001, dict) or rt001.get("b_protocol_rehearsal") != "CLOSED":
        errors.append("RT-001 protocol rehearsal must be CLOSED")
    if isinstance(rt001, dict):
        if rt001.get("b1_protocol_rehearsal") not in (None, rt001.get("b_protocol_rehearsal")):
            errors.append("b1_protocol_rehearsal must alias b_protocol_rehearsal")
        if rt001.get("b2_criterion_dual_rater") not in (None, rt001.get("b_criterion_dual_rater")):
            errors.append("b2_criterion_dual_rater must alias b_criterion_dual_rater")
    if not isinstance(rt001, dict) or int(rt001.get("independent_human_raters") or 0) != 0:
        errors.append("must not invent independent human raters in git")
    if not isinstance(rt002, dict) or rt002.get("a_regulatory") != "CLOSED":
        errors.append("RT-002a regulatory must stay CLOSED")
    if not isinstance(rt002, dict) or rt002.get("b_eir_carrier") != "CLOSED":
        errors.append("RT-002b EIR carrier must be CLOSED on the channel pin")
    if not isinstance(rt002, dict) or rt002.get("b_corporate") != "OPEN":
        errors.append("RT-002c signed corporate IDS must stay OPEN")
    if not isinstance(rt002, dict) or rt002.get("c_corporate_signed") != "OPEN":
        errors.append("RT-002c c_corporate_signed must stay OPEN")
    if isinstance(rt002, dict) and rt002.get("customer_approved_ids") is True:
        errors.append("must not invent customer_approved IDS in git")
    if isinstance(rt002, dict) and rt002.get("eir_v4_present") is not True:
        errors.append("RT-002b needs eir_v4_present on the deep-study pin")
    if isinstance(rt002, dict) and rt002.get("bim_standard_v4_present") is not True:
        errors.append("RT-002b needs bim_standard_v4_present on the deep-study pin")
    if isinstance(rt002, dict) and rt002.get("eir_lod_mep_disciplines_named") is not True:
        errors.append("EIR LOD MEP discipline names must stay pinned from the cartography")
    if isinstance(rt002, dict) and rt002.get("pointer_samolet_alias") is True:
        errors.append("jurisdiction pointer must not alias Samolet")
    counts = rt002.get("ids_counts") if isinstance(rt002, dict) else None
    if not isinstance(counts, dict):
        errors.append("RT-002a must pin public IDS counts")
    else:
        if int(counts.get("moexp") or 0) < MIN_MOEXP_IDS:
            errors.append("RT-002a needs MosoblGosExpertiza IDS in samples/")
        if int(counts.get("spb_cge") or 0) < MIN_SPB_IDS:
            errors.append("RT-002a needs SPb GAU CGE IDS in samples/")
        if int(counts.get("moscow_agr") or 0) < MIN_AGR_IDS:
            errors.append("RT-002a needs city AGR IDS in samples/")
    if not isinstance(rt003, dict) or rt003.get("a_federated_geometric_rehearsal") != "CLOSED":
        errors.append("RT-003a planted geometric rehearsal must be CLOSED")
    if not isinstance(rt003, dict) or rt003.get("b_navis_federation_carrier") != "CLOSED":
        errors.append("RT-003 NWD federation carrier must be CLOSED on the channel pin")
    if not isinstance(rt003, dict) or rt003.get("b_ifc_system_graph_rehearsal") != "CLOSED":
        errors.append("RT-003b IfcSystem graph rehearsal must be CLOSED on the HVAC fixture")
    if not isinstance(rt003, dict) or rt003.get("b_mep_system_clash") != "OPEN":
        errors.append("RT-003c mep_system_clash must stay OPEN")
    if isinstance(rt003, dict):
        if rt003.get("b1_navis_federation_carrier") not in (
            None,
            rt003.get("b_navis_federation_carrier"),
        ):
            errors.append("b1_navis_federation_carrier must alias b_navis_federation_carrier")
        if rt003.get("b2_ifc_system_graph_rehearsal") not in (
            None,
            rt003.get("b_ifc_system_graph_rehearsal"),
        ):
            errors.append("b2_ifc_system_graph_rehearsal must alias b_ifc_system_graph_rehearsal")
        if rt003.get("b3_mep_system_clash") not in (None, rt003.get("b_mep_system_clash")):
            errors.append("b3_mep_system_clash must alias b_mep_system_clash")
    if isinstance(rt003, dict) and rt003.get("mep_system_clash") != "NOT_VERIFIED":
        errors.append("planted pin must keep mep_system_clash=NOT_VERIFIED")
    if isinstance(rt003, dict) and int(rt003.get("nwd_federation_count") or 0) < 3:
        errors.append("RT-003 navis carrier needs nwd_federation_count>=3")
    if isinstance(rt003, dict) and rt003.get("parse_rvt_nwd_lira") is True:
        errors.append("must not claim native NWD parse")
    present = payload.get("evidence_present")
    if isinstance(present, dict):
        missing = [name for name, ok in present.items() if not ok]
        if missing:
            errors.append("missing evidence: " + ", ".join(missing))
    if errors:
        raise RtBlockerVolumeError("; ".join(errors))
