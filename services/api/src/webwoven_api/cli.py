"""Command-line entry point for local API development."""


def run() -> None:
    """Start the application with production-safe proxy header handling."""
    import uvicorn

    uvicorn.run(
        "webwoven_api.main:create_app",
        host="127.0.0.1",
        port=8000,
        proxy_headers=True,
        factory=True,
    )
