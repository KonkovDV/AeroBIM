"""Filesystem JSON loader for package inventory (WP-05)."""

from __future__ import annotations

import json
from pathlib import Path

from aerobim.domain.package_completeness import (
    INVENTORY_SCHEMA_V1,
    PackageCompletenessReport,
    PackageInventory,
    assess_package_completeness,
)


class JsonPackageInventoryLoader:
    """Load ``aerobim_package_inventory_v1`` JSON and assess completeness."""

    def load(self, inventory_path: Path) -> PackageInventory:
        if not inventory_path.is_file():
            raise FileNotFoundError(inventory_path)
        payload = json.loads(inventory_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("package inventory must be a JSON object")
        inventory = PackageInventory.from_mapping(payload)
        if inventory.schema != INVENTORY_SCHEMA_V1:
            # Still return; assess() will emit a fail-closed schema ERROR.
            return inventory
        return inventory

    def assess(self, inventory_path: Path) -> PackageCompletenessReport:
        return assess_package_completeness(self.load(inventory_path))
