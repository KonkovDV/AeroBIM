"""Two license lanes: public MIT tree vs Samolet-local copyleft inputs.

Not a legal opinion. Does not close RT-001/002/003. Does not enable native DWG.
"""

from __future__ import annotations

# IFC-Bench v2 project dirs that are GNU GPLv3 (must not enter the MIT git tree).
GPLV3_IFC_BENCH_PROJECTS: tuple[str, ...] = (
    "4351",
    "ettenheim_gis",
    "hitos",
    "samuel_macalister_sample_house",
)


def local_samolet_demo_copyleft_inputs_permitted(*, opted_in: bool, ci: bool) -> bool:
    """GPLv3 IFC files may be read from gitignored ``.local/`` for a Samolet demo.

    Off by default. Forced off in CI. Never a reason to vendor those files into git
    or to ship LibreDWG/AGPL in the public runtime lock / Docker image.
    """
    return bool(opted_in) and not bool(ci)
