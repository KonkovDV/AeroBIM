"""Outbound URL safety for JWKS / bSI / OpenCDE / custom S3 endpoints (SSRF guard).

Config-sourced URLs still must not resolve to loopback, RFC1918, link-local,
multicast, CGNAT, or cloud metadata addresses. Redirects are rejected so an open
redirect cannot pivot into a blocked network after the initial allow check.
DNS is resolved once and the connection is pinned to a validated IP.
"""

from __future__ import annotations

import http.client
import ipaddress
import socket
import ssl
from dataclasses import dataclass
from urllib.error import URLError
from urllib.parse import urlparse, urlunparse
from urllib.request import (
    HTTPHandler,
    HTTPRedirectHandler,
    HTTPSHandler,
    OpenerDirector,
    Request,
    build_opener,
)

_BLOCKED_NETWORKS: tuple[ipaddress.IPv4Network | ipaddress.IPv6Network, ...] = (
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("100.64.0.0/10"),
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


@dataclass(frozen=True)
class PinnedOutboundUrl:
    """Validated outbound target with DNS pinned to a single safe IP."""

    url: str
    hostname: str
    pinned_ip: str
    port: int
    scheme: str


class _RejectRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        raise UnsafeOutboundUrlError(f"Outbound HTTP redirects are not allowed ({code} → {newurl})")


def _is_blocked_ip(address: str) -> bool:
    try:
        ip = ipaddress.ip_address(address)
    except ValueError:
        return False
    # is_global=False covers RFC1918, loopback, link-local, CGNAT 100.64/10, etc.
    if not ip.is_global:
        return True
    if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved:
        return True
    return any(ip in network for network in _BLOCKED_NETWORKS)


def _format_netloc(ip: str, port: int, *, scheme: str, explicit_port: bool) -> str:
    if ":" in ip and not ip.startswith("["):
        host = f"[{ip}]"
    else:
        host = ip
    default_port = 443 if scheme == "https" else 80
    if explicit_port or port != default_port:
        return f"{host}:{port}"
    return host


def assert_safe_outbound_url(
    url: str,
    *,
    allow_http: bool = False,
    resolve_dns: bool = True,
) -> str:
    """Validate *url* for outbound server-side fetches. Returns the stripped URL."""

    pinned = resolve_and_pin_outbound_url(url, allow_http=allow_http, resolve_dns=resolve_dns)
    return pinned.url


_LOCAL_DATASTORE_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})


def assert_oidc_jwks_host_bound(
    issuer: str,
    jwks_url: str,
    extra_hosts: tuple[str, ...] | list[str] = (),
) -> None:
    """Require JWKS hostname to match issuer hostname (or an explicit extra allowlist).

    Known multi-host IdPs can list alternate JWKS hosts via
    ``AEROBIM_OIDC_JWKS_EXTRA_HOSTS``.
    """
    issuer_host = urlparse(issuer.strip()).hostname if isinstance(issuer, str) else None
    jwks_host = urlparse(jwks_url.strip()).hostname if isinstance(jwks_url, str) else None
    if not issuer_host or not jwks_host:
        raise UnsafeOutboundUrlError(
            "OIDC issuer and JWKS URL must both include hostnames for host binding"
        )
    issuer_norm = issuer_host.lower()
    jwks_norm = jwks_host.lower()
    if issuer_norm == jwks_norm:
        return
    allowed = {host.strip().lower() for host in extra_hosts if host and host.strip()}
    if jwks_norm in allowed:
        return
    raise UnsafeOutboundUrlError(
        f"OIDC JWKS host {jwks_host!r} does not match issuer host {issuer_host!r} "
        "and is not listed in AEROBIM_OIDC_JWKS_EXTRA_HOSTS"
    )


def assert_safe_datastore_url(url: str, *, resolve_dns: bool = True) -> str:
    """Validate Redis / Postgres connection URLs at settings load (RTATOM-I09/I10).

    Localhost and unix sockets are skipped. Remote hosts are gated via the same
    SSRF host checks as HTTP outbound URLs (scheme rewritten to https for reuse).
    """

    if not isinstance(url, str) or not url.strip():
        raise UnsafeOutboundUrlError("Datastore URL must be a non-empty string")
    cleaned = url.strip()
    lowered = cleaned.lower()
    # Unix-domain sockets: redis+unix://, unix://, or libpq host=/path forms.
    if (
        lowered.startswith("unix:")
        or lowered.startswith("redis+unix:")
        or "host=/ " in lowered
        or "host=/" in lowered
        or lowered.startswith("postgresql:///")
        or lowered.startswith("postgres:///")
    ):
        return cleaned

    parsed = urlparse(cleaned)
    host = parsed.hostname
    if host is None or not host.strip():
        raise UnsafeOutboundUrlError("Datastore URL must include a hostname or unix socket")
    if host.lower() in _LOCAL_DATASTORE_HOSTS:
        return cleaned

    # Reuse HTTP SSRF host/IP policy (blocks metadata, CGNAT, RFC1918, etc.).
    assert_safe_outbound_url(f"https://{host}/", allow_http=False, resolve_dns=resolve_dns)
    return cleaned


def resolve_and_pin_outbound_url(
    url: str,
    *,
    allow_http: bool = False,
    resolve_dns: bool = True,
) -> PinnedOutboundUrl:
    """Validate *url* and optionally resolve+pin DNS to a single safe address."""

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

    port = parsed.port or (443 if parsed.scheme == "https" else 80)

    # Literal IP in hostname.
    try:
        if _is_blocked_ip(host):
            raise UnsafeOutboundUrlError(f"Outbound host resolves to blocked address: {host}")
        # Literal IP host — pin to itself without DNS.
        return PinnedOutboundUrl(
            url=cleaned,
            hostname=host,
            pinned_ip=str(ipaddress.ip_address(host)),
            port=port,
            scheme=parsed.scheme,
        )
    except UnsafeOutboundUrlError:
        raise
    except ValueError:
        pass

    pinned_ip = host
    if resolve_dns:
        try:
            infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
        except socket.gaierror as exc:
            raise UnsafeOutboundUrlError(f"Outbound host DNS resolution failed: {host}") from exc
        if not infos:
            raise UnsafeOutboundUrlError(
                f"Outbound host DNS resolution returned no addresses: {host}"
            )
        chosen: str | None = None
        for info in infos:
            address = str(info[4][0])
            if _is_blocked_ip(address):
                raise UnsafeOutboundUrlError(
                    f"Outbound host {host!r} resolves to blocked address {address}"
                )
            if chosen is None:
                chosen = address
        assert chosen is not None
        pinned_ip = chosen

    return PinnedOutboundUrl(
        url=cleaned,
        hostname=host,
        pinned_ip=pinned_ip,
        port=port,
        scheme=parsed.scheme,
    )


def safe_urlopen(request: Request, *, timeout: float, allow_http: bool = False):
    """``urlopen`` wrapper: SSRF host check, DNS pin, no redirects, no second DNS."""

    pinned = resolve_and_pin_outbound_url(request.full_url, allow_http=allow_http, resolve_dns=True)
    parsed = urlparse(pinned.url)
    explicit_port = parsed.port is not None
    netloc = _format_netloc(
        pinned.pinned_ip, pinned.port, scheme=pinned.scheme, explicit_port=explicit_port
    )
    pinned_url = urlunparse(
        (
            pinned.scheme,
            netloc,
            parsed.path or "",
            parsed.params,
            parsed.query,
            parsed.fragment,
        )
    )

    headers = {key: value for key, value in request.header_items()}
    host_header = pinned.hostname if not explicit_port else f"{pinned.hostname}:{pinned.port}"
    headers["Host"] = host_header
    pinned_request = Request(
        pinned_url,
        data=request.data,
        headers=headers,
        method=request.get_method(),
    )

    if pinned.scheme == "https":
        context = ssl.create_default_context()
        server_hostname = pinned.hostname

        class _PinnedHTTPSConnection(http.client.HTTPSConnection):
            def connect(self) -> None:  # noqa: ANN201 — stdlib signature
                sock = socket.create_connection((self.host, self.port), self.timeout)
                if self._tunnel_host:  # type: ignore[attr-defined]
                    self.sock = sock
                    self._tunnel()  # type: ignore[misc]
                    sock = self.sock  # type: ignore[assignment]
                self.sock = context.wrap_socket(sock, server_hostname=server_hostname)

        class _PinnedHTTPSHandler(HTTPSHandler):
            def https_open(self, req):  # type: ignore[no-untyped-def]
                return self.do_open(_PinnedHTTPSConnection, req)

        opener: OpenerDirector = build_opener(
            _RejectRedirects,
            _PinnedHTTPSHandler(context=context),
        )
    else:
        opener = build_opener(_RejectRedirects, HTTPHandler())

    try:
        return opener.open(pinned_request, timeout=timeout)
    except URLError as exc:
        raise UnsafeOutboundUrlError(f"Outbound request failed: {exc}") from exc


__all__ = [
    "PinnedOutboundUrl",
    "UnsafeOutboundUrlError",
    "assert_oidc_jwks_host_bound",
    "assert_safe_datastore_url",
    "assert_safe_outbound_url",
    "resolve_and_pin_outbound_url",
    "safe_urlopen",
]
