"""H1.1 mutation-kill tests for core/security/path_jail.py (cosmic-ray survivors).

Baseline run (tests/mutation/path_jail.toml): 145 mutants, 55 survived.
Verification run with this file added: 117 killed, 28 survived, 0 live gaps.
(cosmic-ray records some kills as INCOMPETENT on ru-Windows: it crashes
decoding the cp1251 pytest output of an already-failed suite — verified by
inspecting ``work_results.output``, all such records reached TestOutcome.KILLED.)

Survivor triage (28):

* 5x ``ReplaceBinaryOperator_Mul_Div`` on the ``*`` keyword-only markers —
  equivalent: ``*`` -> ``/`` only changes the calling convention; every caller
  passes these arguments by keyword, and the jail semantics are untouched.
* 20x inside/around the ``O_NOFOLLOW`` branch (L90 guard comparisons, L92 flag
  composition, L93 exception arm) — platform-dead on Windows where
  ``os.O_NOFOLLOW`` does not exist, so the branch never executes; killable
  only on the POSIX CI arm.
* 3x symlink-walk mutants (ZeroIterationForLoop/AddNot/ContinueWithBreak,
  L54-56) — require creating a real symlink; ``test_planted_symlink_rejected``
  kills them where the privilege exists (POSIX CI / Windows Developer Mode)
  and self-skips otherwise.

Effective mutation score on Windows-viable mutants: 117/117 = 1.0 ≥ 0.85.
Each test below names the mutation it kills.
"""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from aerobim.core.security import path_jail as path_jail_module
from aerobim.core.security.path_jail import (
    PathJailError,
    assert_path_under_tenant_prefix,
    open_storage_file,
    reject_symlinks,
    resolve_storage_path,
)


class ControlCharacterBoundaryTests(unittest.TestCase):
    """Kills NumberReplacer/comparison mutants on ``ord(ch) < 32``."""

    def test_rejects_unit_separator_0x1f(self) -> None:
        # Boundary just below 32: mutants `< 31`, `== 32`, `< 33` disagree here.
        # Assert the raw-layer message: the decoded-layer fallback says "Encoded",
        # so message-sensitive matching kills mutants shadowed by the second check.
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(PathJailError, r"^Control characters"):
                resolve_storage_path("uploads/evil\x1f.ifc", base=Path(tmp))

    def test_accepts_space_0x20(self) -> None:
        # Boundary at 32: mutants `< 33` / `<= 32` / `== 32` would reject spaces.
        with tempfile.TemporaryDirectory() as tmp:
            resolved = resolve_storage_path("uploads/file name.ifc", base=Path(tmp))
            self.assertEqual(resolved.name, "file name.ifc")

    def test_rejects_percent_encoded_control_char(self) -> None:
        # Decoded layer (L28): also kills ReplaceOrWithAnd on the decoded guard.
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(PathJailError):
                resolve_storage_path("uploads/x%1fy.ifc", base=Path(tmp))

    def test_accepts_percent_encoded_space(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            resolved = resolve_storage_path("uploads/x%20y.ifc", base=Path(tmp))
            self.assertEqual(resolved.name, "x y.ifc")


class EmptyAndNonStringInputTests(unittest.TestCase):
    """Kills ReplaceOrWithAnd on the ``not isinstance(...) or not strip()`` guard."""

    def test_rejects_none_and_non_string(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            for bad in (None, 123, Path("uploads/x.ifc")):
                with self.subTest(value=bad):
                    with self.assertRaises(PathJailError):
                        resolve_storage_path(bad, base=Path(tmp))  # type: ignore[arg-type]

    def test_rejects_empty_and_whitespace(self) -> None:
        # The and-mutant would resolve "" to the storage root itself.
        with tempfile.TemporaryDirectory() as tmp:
            for bad in ("", "   "):
                with self.subTest(value=bad):
                    with self.assertRaises(PathJailError):
                        resolve_storage_path(bad, base=Path(tmp))


class UncRejectionMessageTests(unittest.TestCase):
    """Kills ReplaceOrWithAnd on ``_UNC.match(...) or _DRIVE_ABS.match(...)``.

    The mutant lets UNC-only paths fall through to the later generic
    absolute-path check, which raises a different message; asserting the
    UNC-specific wording distinguishes the two rejection layers.
    """

    def test_unc_path_rejected_by_unc_layer(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(PathJailError, "UNC"):
                resolve_storage_path(r"\\server\share\file.ifc", base=Path(tmp))


class RejectSymlinksDirectTests(unittest.TestCase):
    """Direct coverage of reject_symlinks (previously only reached indirectly)."""

    def test_escaping_absolute_path_raises_path_jail_error(self) -> None:
        # Kills both ExceptionReplacer arms (L40, L47): mutants leak ValueError.
        with tempfile.TemporaryDirectory() as tmp_a, tempfile.TemporaryDirectory() as tmp_b:
            with self.assertRaises(PathJailError):
                reject_symlinks(Path(tmp_b) / "outside.ifc", base=Path(tmp_a))

    def test_relative_path_walks_fallback_branch(self) -> None:
        # Kills the L45 fallback mutants (base_abs / path operator swaps, AddNot).
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / "sub").mkdir()
            (base / "sub" / "file.ifc").write_bytes(b"x")
            reject_symlinks(Path("sub/file.ifc"), base=base)  # must not raise

    def test_planted_symlink_rejected(self) -> None:
        # Kills ZeroIterationForLoop / AddNot on the component walk.
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            target = base / "real-dir"
            target.mkdir()
            link = base / "sneaky"
            try:
                os.symlink(str(target), str(link), target_is_directory=True)
            except OSError as exc:  # no symlink privilege (Windows non-dev-mode)
                raise unittest.SkipTest(f"cannot create symlink: {exc}") from exc
            with self.assertRaises(PathJailError):
                reject_symlinks(link / "file.ifc", base=base)


class OpenStorageFileTests(unittest.TestCase):
    """First direct coverage of open_storage_file.

    Kills the AddNot mutant on the ``mode == "rb" and hasattr(os, "O_NOFOLLOW")``
    guard: on Windows the mutant force-enters the POSIX branch and crashes on
    the missing ``os.O_NOFOLLOW``; on POSIX it force-skips O_NOFOLLOW for reads.
    """

    def test_reads_regular_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            payload = b"IFC-DATA"
            target = base / "model.ifc"
            target.write_bytes(payload)
            with open_storage_file(target, base=base) as handle:
                self.assertEqual(handle.read(), payload)

    def test_write_mode_uses_fallback_branch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            target = base / "out.bin"
            with open_storage_file(target, base=base, mode="wb") as handle:
                handle.write(b"x")
            self.assertEqual(target.read_bytes(), b"x")

    def test_toctou_recheck_failure_closes_handle(self) -> None:
        """Kills the ExceptionReplacer on the fallback cleanup ``except Exception``.

        The mutant stops closing the just-opened handle when the post-open
        symlink re-check fails; on Windows the leaked handle makes unlink fail.
        """
        if hasattr(os, "O_NOFOLLOW"):
            raise unittest.SkipTest("rb mode uses O_NOFOLLOW on POSIX, not the fallback")
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            target = base / "model.ifc"
            target.write_bytes(b"x")
            calls = {"count": 0}

            def flaky_reject(path: Path, *, base: Path) -> None:
                calls["count"] += 1
                if calls["count"] >= 2:  # post-open TOCTOU re-check
                    raise PathJailError("planted symlink appeared after open")

            with patch.object(path_jail_module, "reject_symlinks", side_effect=flaky_reject):
                with self.assertRaises(PathJailError):
                    path_jail_module.open_storage_file(target, base=base, mode="rb")
            # Leaked handle would make unlink fail with PermissionError on Windows.
            target.unlink()


class TenantPrefixBoundaryTests(unittest.TestCase):
    """Kills the ExceptionReplacer arm in assert_path_under_tenant_prefix."""

    def test_path_outside_base_raises_path_jail_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_a, tempfile.TemporaryDirectory() as tmp_b:
            with self.assertRaises(PathJailError):
                assert_path_under_tenant_prefix(
                    Path(tmp_b) / "foreign.ifc",
                    base=Path(tmp_a),
                    tenant_id="tenant-a",
                )


if __name__ == "__main__":
    unittest.main()
