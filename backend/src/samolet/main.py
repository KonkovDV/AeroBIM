from __future__ import annotations


def _create_app():
    """Lazy app factory — avoids side-effects at import time."""
    from samolet.infrastructure.di.bootstrap import bootstrap_container
    from samolet.presentation.http.api import create_http_app

    container = bootstrap_container()
    return container, create_http_app(container)


def main() -> None:
    try:
        import uvicorn
    except ModuleNotFoundError as exc:
        raise SystemExit("Install backend dependencies before starting the API") from exc

    from samolet.core.di.tokens import Tokens

    container, app = _create_app()
    settings = container.resolve(Tokens.SETTINGS)
    uvicorn.run(app, host=settings.host, port=settings.port)


if __name__ == "__main__":
    main()
