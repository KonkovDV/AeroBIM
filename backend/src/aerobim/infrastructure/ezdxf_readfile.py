"""Load DXF via ezdxf without touching the incomplete ``ezdxf.readfile`` stub.

``ezdxf.readfile`` is a lazy re-export. When the package is installed, mypy
reports that the top-level module does not explicitly export ``readfile``.
``getattr`` is the typed access; behaviour is unchanged.

This module lives outside ``infrastructure/adapters/`` so it is not counted as
an adapter in the live architecture inventory.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def ezdxf_readfile(path: Path | str) -> Any:
    """Open a DXF document. Caller must already have imported ezdxf successfully."""

    import ezdxf

    reader = getattr(ezdxf, "readfile", None)
    if not callable(reader):
        raise AttributeError("ezdxf.readfile is not available on this install")
    return reader(str(path))
