"""Minimal CAD fixtures.

- `minimal-entities.dxf` — LINE + TEXT for ezdxf ingest (TZ row 4).
- `placeholder-source.dwg` — fake DWG bytes, not a native parse target.
- `placeholder-source.dwg.derived-provenance.json` — hash-bound DWG→DXF
  substitute. Verified pair never makes ``dwg_dxf`` OK (TZ row 3 stays MISSING).
"""
