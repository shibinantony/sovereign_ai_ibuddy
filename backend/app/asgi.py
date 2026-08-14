"""Production ASGI entry point kept separate from the testable app factory."""

from backend.app.main import create_app

app = create_app()
