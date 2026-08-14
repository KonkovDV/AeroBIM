<!-- claims-lint: allow-file reason="Open federated duplex IfcClash pin; RT-003 stays OPEN" -->
---
title: "IFC-Bench duplex federated IfcClash pin"
claim_level: open_bench_only
closes_rt003: false
mep_system_clash: NOT_VERIFIED
---

# IFC-Bench duplex federated IfcClash

- closes_rt003: **False**
- mep_system_clash: **NOT_VERIFIED**
- content_sha256: `d87f8e0206fd88306aa617386319cc326751cbd17f70aa6a52091a40151193c6`

| label | status | clash_count |
| --- | --- | ---: |
| duplex_arc_vs_mep | RUN | 837 |

Hashed IfcClash on gitignored IFC-Bench duplex ARC vs MEP. Public federated pair, no coordinator BCF gold, no signed clearance matrix, not customer models, not MEP system-aware. Hits ≠ delivered. Checkpoint NO_GO.
