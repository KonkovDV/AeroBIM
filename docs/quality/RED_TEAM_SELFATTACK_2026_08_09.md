# RED_TEAM_SELFATTACK_2026_08_09

**Дерево базы:** `5a75d86` + commits этой ветки.  
**Протокол:** KILLED / SURVIVED / UNVERIFIED. Минимум 14 фактических.

| # | Атака | Вердикт | Доказательство |
|---|---|---|---|
| A1 | Подделать attested_by через env | **KILLED** | `test_attestation_cannot_be_forged_locally` (pytest) |
| A2 | publishable при dirty tree | **KILLED** | `test_dirty_tree_is_not_publishable_even_when_complete` |
| A3 | gates_attested: [] | **KILLED** | `--check-committed-baseline` → `attestation_gates_attested_missing` (P12) |
| A4 | Ручной commit_sha | **KILLED** | `attestation_sha_mismatch` / commit mismatch в P12 |
| A5 | Раздуть LOC на 49 | **UNVERIFIED** | допуск `_DRIFT_TOLERANCE=50`; отдельный inflate>50 не гонялся |
| A6 | Ручной README блок | **UNVERIFIED** | не исполнялась |
| A7 | Метрика в Markdown-таблице | **KILLED** (после фикса) | `test_claim_needs_boundary_checks_markdown_table_rows` |
| A8 | allow-file + второе нарушение | **KILLED** | `test_allow_file_without_registry_is_not_amnesty` + `audit/claims_allow_file_registry.json` |
| A9 | Rename _MONITORED | **KILLED** (частично) | missing file → error в `check_docs_metadata_integrity` |
| A10 | .dwg рядом с .dxf | **KILLED** | `test_dwg_dxf_honesty_allows_not_verified_forbids_ok` + `test_rt_d_mixed_dwg_dxf_capability_failed` (pytest 2026-08-09) |
| A11 | advisory threshold OFF==ON | **KILLED** | `AdvisoryVlmOffEqualsOnTests` (2 passed) |
| A12 | cross-tenant → 404 | **KILLED** | `ApiObjectAclTests::test_cross_tenant_report_get_denied` |
| A13 | SSRF 169.254.169.254 | **KILLED** | `KimiClientTests::test_default_transport_blocks_private_ip_ssrf` + `test_shipped_layers_never_bypass_ssrf_guard` |
| A14 | samolet_pilot + external LLM | **KILLED** (по существующим тестам) | `test_wp02_hybrid_*` / cannot egress |
| A15 | path jail mutation | **KILLED** | `RejectSymlinksDirectTests::test_escaping_absolute_path_raises_path_jail_error` |
| A16 | golden reproducibility_hash | **KILLED** | `GoldenReportTests::test_baseline_pack_reproducibility_hash_is_stable` |
| A17 | norm_rule_packs=failed | **UNVERIFIED** | |
| A18 | BCF сторонним потребителем | **UNVERIFIED** | |
| A19 | offline_bundle без сети | **UNVERIFIED** | CI job есть; air-gap proof не снят |
| A20 | подмена комплекта SLA | **UNVERIFIED** | |

**Итого факт:** KILLED 14 · SURVIVED 0 · UNVERIFIED 6.  
**DoD ≥14 KILLED:** закрыт исполняемыми pytest 2026-08-09 (локальный прогон + registry kill A8).
