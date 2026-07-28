"""RT hyper-deep: OIDC validator build must fail-closed on partial config.

The build previously gated the issuer/audience/jwks_url invariant on ``assert``,
which is stripped under ``python -O``. It now raises explicitly, so the guard
holds under -O and any future refactor of the derived ``oidc_enabled`` property.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from aerobim.infrastructure.di.bootstrap import _build_oidc_validator


def test_returns_none_when_oidc_disabled() -> None:
    settings = SimpleNamespace(
        oidc_enabled=False,
        oidc_issuer=None,
        oidc_audience=None,
        oidc_jwks_url=None,
    )
    assert _build_oidc_validator(settings) is None  # type: ignore[arg-type]


def test_raises_when_enabled_but_partial_config() -> None:
    # oidc_enabled forced True while a field is blank simulates a future refactor
    # of the derived property; the explicit guard must refuse (holds under -O,
    # unlike the previous assert which would be stripped).
    settings = SimpleNamespace(
        oidc_enabled=True,
        oidc_issuer="https://issuer.example",
        oidc_audience="",  # missing -> must not build a partial validator
        oidc_jwks_url="https://issuer.example/jwks",
    )
    with pytest.raises(RuntimeError, match="partial security config"):
        _build_oidc_validator(settings)  # type: ignore[arg-type]
