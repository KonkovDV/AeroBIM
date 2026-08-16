"""Outbound URL safety for JWKS / bSI / OpenCDE / custom S3 endpoints (SSRF guard).

Config-sourced URLs still must not resolve to loopback, RFC1918, link-local,
multicast, CGNAT, or cloud metadata addresses. Redirects are rejected so an open
redirect cannot pivot into a blocked network after the initial allow check.
DNS is resolved once and the connection is pinned to a validated IP.
"""

from __future__ import annotations

import http.client
import ipaddress
import re
import socket
import ssl
from dataclasses import dataclass
from typing import Any
from urllib.error import URLError
from urllib.parse import urlparse, urlunparse
from urllib.request import (
    HTTPHandler,
    HTTPRedirectHandler,
    HTTPSHandler,
    OpenerDirector,
    ProxyHandler,
    Request,
    build_opener,
    urlopen,
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
    ipaddress.ip_network("::/96"),  # IPv4-compatible / degenerate
    ipaddress.ip_network("2001::/32"),  # Teredo
    ipaddress.ip_network("2002::/16"),  # 6to4 (may embed private IPv4)
    ipaddress.ip_network("64:ff9b::/96"),  # NAT64 well-known prefix
    ipaddress.ip_network("64:ff9b:1::/48"),  # NAT64 local-use
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


class _NullProxyHandler(ProxyHandler):
    """Ignore HTTP(S)_PROXY / ALL_PROXY so DNS-pinned IPs are not sent via a proxy."""

    def __init__(self) -> None:
        super().__init__({})


_NONCANONICAL_IPV4_HOST = re.compile(r"^(?:\d+|0x[0-9a-fA-F]+)$")
_DOTTED_IPV4_SHORTHAND = re.compile(r"^(?:\d+|0x[0-9a-fA-F]+)(?:\.(?:\d+|0x[0-9a-fA-F]+)){1,3}$")


def _parse_ipv4_numeric_token(token: str) -> int:
    """Parse one IPv4 token: decimal, ``0x`` hex, or leading-zero octal (BSD inet_aton)."""

    lowered = token.lower()
    if lowered.startswith("0x"):
        return int(token, 16)
    if token.isdigit() and len(token) > 1 and token.startswith("0"):
        return int(token, 8)
    return int(token, 10)


def _dotted_ipv4_shorthand_address(host: str) -> ipaddress.IPv4Address | None:
    """Map ``127.1`` / ``0177.0.0.1`` to an IPv4 address (HD-SEC-03)."""

    parts = host.split(".")
    try:
        nums = [_parse_ipv4_numeric_token(part) for part in parts]
    except ValueError:
        return None
    if any(n < 0 for n in nums):
        return None
    try:
        if len(nums) == 4:
            if any(n > 255 for n in nums):
                return None
            value = (nums[0] << 24) | (nums[1] << 16) | (nums[2] << 8) | nums[3]
        elif len(nums) == 3:
            if nums[0] > 255 or nums[1] > 255 or nums[2] > 0xFFFF:
                return None
            value = (nums[0] << 24) | (nums[1] << 16) | nums[2]
        elif len(nums) == 2:
            if nums[0] > 255 or nums[1] > 0xFFFFFF:
                return None
            value = (nums[0] << 24) | nums[1]
        elif len(nums) == 1:
            if nums[0] > 0xFFFFFFFF:
                return None
            value = nums[0]
        else:
            return None
        return ipaddress.IPv4Address(value)
    except (ValueError, OverflowError):
        return None


def _parse_literal_ip_host(host: str) -> ipaddress.IPv4Address | ipaddress.IPv6Address | None:
    """Interpret hostname as IP, including decimal / ``0x`` integer encodings (RT-SSRF-001)."""

    try:
        return ipaddress.ip_address(host)
    except ValueError:
        pass
    if _NONCANONICAL_IPV4_HOST.fullmatch(host):
        parsed = _dotted_ipv4_shorthand_address(host)
        if parsed is not None:
            return parsed
        try:
            value = int(host, 0)
            if 0 <= value <= 0xFFFFFFFF:
                return ipaddress.ip_address(value)
        except (ValueError, OverflowError):
            return None
    if _DOTTED_IPV4_SHORTHAND.fullmatch(host):
        return _dotted_ipv4_shorthand_address(host)
    return None


def _is_blocked_ip(address: str) -> bool:
    try:
        ip = ipaddress.ip_address(address)
    except ValueError:
        return True
    if ip.version == 6 and ip.ipv4_mapped is not None:
        return _is_blocked_ip(str(ip.ipv4_mapped))
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


_LOCAL_DATASTORE_HOSTS = frozenset(
    {"localhost", "127.0.0.1", "::1", "ip6-localhost", "ip6-loopback", "[::1]"}
)


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


def _is_blocked_datastore_ip(address: str) -> bool:
    """Datastore peers may live on RFC1918/ULA; metadata and link-local stay blocked."""

    try:
        ip = ipaddress.ip_address(address)
    except ValueError:
        return True
    if ip.is_loopback:
        return False
    if ip.is_link_local or ip.is_multicast or ip.is_reserved:
        return True
    if ip.version == 4 and ip in ipaddress.ip_network("0.0.0.0/8"):
        return True
    if ip.version == 6 and ip.ipv4_mapped is not None:
        return _is_blocked_datastore_ip(str(ip.ipv4_mapped))
    return False


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

    literal = _parse_literal_ip_host(host)
    if literal is not None:
        if _is_blocked_datastore_ip(str(literal)):
            raise UnsafeOutboundUrlError(f"Datastore host is blocked: {host}")
        return cleaned

    if resolve_dns:
        port = parsed.port or 6379
        try:
            infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
        except socket.gaierror as exc:
            raise UnsafeOutboundUrlError(f"Datastore host DNS resolution failed: {host}") from exc
        if not infos:
            raise UnsafeOutboundUrlError(
                f"Datastore host DNS resolution returned no addresses: {host}"
            )
        for info in infos:
            address = str(info[4][0])
            if _is_blocked_datastore_ip(address):
                raise UnsafeOutboundUrlError(
                    f"Datastore host {host!r} resolves to blocked address {address}"
                )
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

    literal_ip = _parse_literal_ip_host(host)
    if literal_ip is not None:
        pinned = str(literal_ip)
        if _is_blocked_ip(pinned):
            raise UnsafeOutboundUrlError(f"Outbound host resolves to blocked address: {host}")
        return PinnedOutboundUrl(
            url=cleaned,
            hostname=host,
            pinned_ip=pinned,
            port=port,
            scheme=parsed.scheme,
        )

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


def _open_pinned(request: Request, *, timeout: float, allow_http: bool) -> Any:
    opener: OpenerDirector
    if request.full_url.lower().startswith("https:"):
        context = ssl.create_default_context()
        # Host header already set by caller to original hostname for SNI/cert.
        server_hostname = request.get_header("Host") or ""
        if ":" in server_hostname and not server_hostname.startswith("["):
            server_hostname = server_hostname.rsplit(":", 1)[0]
        server_hostname = server_hostname.strip("[]")

        class _PinnedHTTPSConnection(http.client.HTTPSConnection):
            def connect(self) -> None:  # noqa: ANN201 — stdlib signature
                sock = socket.create_connection((self.host, self.port), self.timeout)
                tunnel_host = getattr(self, "_tunnel_host", None)
                if tunnel_host:
                    self.sock = sock
                    tunnel = getattr(self, "_tunnel", None)
                    if callable(tunnel):
                        tunnel()
                    sock = self.sock
                self.sock = context.wrap_socket(sock, server_hostname=server_hostname)

        class _PinnedHTTPSHandler(HTTPSHandler):
            def https_open(self, req):  # type: ignore[no-untyped-def]
                return self.do_open(_PinnedHTTPSConnection, req)

        opener = build_opener(
            _NullProxyHandler(), _RejectRedirects, _PinnedHTTPSHandler(context=context)
        )
    else:
        if not allow_http:
            raise UnsafeOutboundUrlError("HTTP outbound is disabled")
        opener = build_opener(_NullProxyHandler(), _RejectRedirects, HTTPHandler())
    return opener.open(request, timeout=timeout)


def safe_datastore_urlopen(request: Request, *, timeout: float) -> Any:
    """Loopback / unix-datastore ``urlopen`` after :func:`assert_safe_datastore_url`.

    Public :func:`safe_urlopen` rejects loopback by design. Local vLLM must still
    go through this seam so adapters never call raw ``urlopen`` themselves
    (outbound-guard invariant). HTTP(S) peers are DNS-pinned (HD-SEC-01).
    """

    url = request.full_url
    assert_safe_datastore_url(url, resolve_dns=True)
    parsed = urlparse(url)
    if parsed.scheme in {"http", "https"}:
        host = parsed.hostname
        if host is None:
            raise UnsafeOutboundUrlError("Datastore URL must include a hostname")
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        literal = _parse_literal_ip_host(host)
        if literal is not None:
            pinned_ip = str(literal)
        else:
            try:
                infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
            except socket.gaierror as exc:
                raise UnsafeOutboundUrlError(
                    f"Datastore host DNS resolution failed: {host}"
                ) from exc
            if not infos:
                raise UnsafeOutboundUrlError(
                    f"Datastore host DNS resolution returned no addresses: {host}"
                )
            pinned_ip = str(infos[0][4][0])
            if _is_blocked_datastore_ip(pinned_ip):
                raise UnsafeOutboundUrlError(
                    f"Datastore host {host!r} resolves to blocked address {pinned_ip}"
                )
        explicit_port = parsed.port is not None
        netloc = _format_netloc(pinned_ip, port, scheme=parsed.scheme, explicit_port=explicit_port)
        pinned_url = urlunparse(
            (
                parsed.scheme,
                netloc,
                parsed.path or "",
                parsed.params,
                parsed.query,
                parsed.fragment,
            )
        )
        headers = {key: value for key, value in request.header_items()}
        headers["Host"] = host if not explicit_port else f"{host}:{port}"
        pinned_request = Request(
            pinned_url,
            data=request.data,
            headers=headers,
            method=request.get_method(),
        )
        try:
            return _open_pinned(pinned_request, timeout=timeout, allow_http=parsed.scheme == "http")
        except URLError as exc:
            raise UnsafeOutboundUrlError(f"Datastore request failed: {exc}") from exc
    return urlopen(request, timeout=timeout)  # noqa: S310 — unix / non-HTTP after jail


def safe_urlopen(request: Request, *, timeout: float, allow_http: bool = False) -> Any:
    """``urlopen`` wrapper: SSRF host check, DNS pin, no redirects, no second DNS, no env proxy."""

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
    try:
        return _open_pinned(pinned_request, timeout=timeout, allow_http=allow_http)
    except URLError as exc:
        raise UnsafeOutboundUrlError(f"Outbound request failed: {exc}") from exc


__all__ = [
    "PinnedOutboundUrl",
    "UnsafeOutboundUrlError",
    "assert_oidc_jwks_host_bound",
    "assert_safe_datastore_url",
    "assert_safe_outbound_url",
    "resolve_and_pin_outbound_url",
    "safe_datastore_urlopen",
    "safe_urlopen",
]
