"""Outbound URL safety for JWKS / bSI / OpenCDE / custom S3 endpoints (SSRF guard).

Config-sourced URLs still must not resolve to loopback, RFC1918, link-local,
multicast, or cloud metadata addresses. Redirects are rejected so an open
redirect cannot pivot into a blocked network after the initial allow check.
"""

from __future__ import annotations

import ipaddress
import socket
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import (
    HTTPRedirectHandler,
    HTTPSHandler,
    OpenerDirector,
    Request,
    build_opener,
)

_BLOCKED_NETWORKS: tuple[ipaddress.IPv4Network | ipaddress.IPv6Network, ...] = (
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
    ipaddress.ip_network("ff00::/8"),
)


class UnsafeOutboundUrlError(ValueError):
    """Raised when an outbound URL fails SSRF / redirect policy checks."""


class _RejectRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        raise UnsafeOutboundUrlError(f"Outbound HTTP redirects are not allowed ({code} → {newurl})")


def _is_blocked_ip(address: str) -> bool:
    try:
        ip = ipaddress.ip_address(address)
    except ValueError:
        return False
    if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved:
        return True
    return any(ip in network for network in _BLOCKED_NETWORKS)


def assert_safe_outbound_url(
    url: str,
    *,
    allow_http: bool = False,
    resolve_dns: bool = True,
) -> str:
    """Validate *url* for outbound server-side fetches. Returns the stripped URL."""

    if not isinstance(url, str) or not url.strip():
        raise UnsafeOutboundUrlError("Outbound URL must be a non-empty string")
    cleaned = url.strip()
    parsed = urlparse(cleaned)
    allowed_schemes = {"https"} if not allow_http else {"https", "http"}
    if parsed.scheme not in allowed_schemes:
        raise UnsafeOutboundUrlError(
            f"Outbound URL scheme must be one of {sorted(allowed_schemes)}; got {parsed.scheme!r}"
        )
    if parsed.username is not None or parsed.password is not None:
        raise UnsafeOutboundUrlError("Outbound URL must not contain userinfo credentials")
    host = parsed.hostname
    if host is None or not host.strip():
        raise UnsafeOutboundUrlError("Outbound URL must include a hostname")
    if host.lower() in {"localhost", "metadata.google.internal"}:
        raise UnsafeOutboundUrlError(f"Outbound host is blocked: {host}")

    # Literal IP in hostname.
    try:
        if _is_blocked_ip(host):
            raise UnsafeOutboundUrlError(f"Outbound host resolves to blocked address: {host}")
    except UnsafeOutboundUrlError:
        raise
    except ValueError:
        pass

    if resolve_dns:
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        try:
            infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
        except socket.gaierror as exc:
            raise UnsafeOutboundUrlError(f"Outbound host DNS resolution failed: {host}") from exc
        if not infos:
            raise UnsafeOutboundUrlError(
                f"Outbound host DNS resolution returned no addresses: {host}"
            )
        for info in infos:
            address = info[4][0]
            if _is_blocked_ip(str(address)):
                raise UnsafeOutboundUrlError(
                    f"Outbound host {host!r} resolves to blocked address {address}"
                )
    return cleaned


def safe_urlopen(request: Request, *, timeout: float, allow_http: bool = False):
    """``urlopen`` wrapper: SSRF host check + no redirects."""

    assert_safe_outbound_url(request.full_url, allow_http=allow_http, resolve_dns=True)
    opener: OpenerDirector = build_opener(_RejectRedirects, HTTPSHandler())
    try:
        return opener.open(request, timeout=timeout)
    except URLError as exc:
        raise UnsafeOutboundUrlError(f"Outbound request failed: {exc}") from exc


__all__ = [
    "UnsafeOutboundUrlError",
    "assert_safe_outbound_url",
    "safe_urlopen",
]
