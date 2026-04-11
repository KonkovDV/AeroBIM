from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aerobim.core.di.container import Container, Lifecycle


class ContainerTests(unittest.TestCase):
    def test_singleton_registration_returns_same_instance(self) -> None:
        container = Container()
        counter = {"value": 0}

        def factory(_container: Container) -> object:
            counter["value"] += 1
            return object()

        container.register("singleton", factory, lifecycle=Lifecycle.SINGLETON)

        first = container.resolve("singleton")
        second = container.resolve("singleton")

        self.assertIs(first, second)
        self.assertEqual(counter["value"], 1)

    def test_transient_registration_returns_new_instance(self) -> None:
        container = Container()
        counter = {"value": 0}

        def factory(_container: Container) -> object:
            counter["value"] += 1
            return object()

        container.register("transient", factory, lifecycle=Lifecycle.TRANSIENT)

        first = container.resolve("transient")
        second = container.resolve("transient")

        self.assertIsNot(first, second)
        self.assertEqual(counter["value"], 2)


if __name__ == "__main__":
    unittest.main()
