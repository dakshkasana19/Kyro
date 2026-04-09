"""
Kyro — Application Entry Point

Usage:
    python run.py
"""

from app.factory import create_app
from app.core.config import settings
from app.core.sockets import socketio

app = create_app()

if __name__ == "__main__":
    socketio.run(
        app,
        host=settings.flask.HOST,
        port=settings.flask.PORT,
        debug=settings.flask.DEBUG,
        use_reloader=settings.flask.DEBUG
    )
