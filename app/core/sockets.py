"""
Kyro — Real-time SocketIO Configuration

Handles bi-directional communication for live queue updates and alerts.
"""

from flask_socketio import SocketIO
from app.core.logging import get_logger

logger = get_logger("core.sockets")

# Singleton SocketIO instance
# CORS is set to "*" for development flexibility; restricted in production.
socketio = SocketIO(cors_allowed_origins="*", async_mode="eventlet")

def notify_new_patient(patient_data: dict):
    """Broadcast a global alert when a new patient enters the system."""
    logger.info("Broadcasting 'patient:new' for %s", patient_data.get("name"))
    socketio.emit("patient:new", patient_data, broadcast=True)

def notify_queue_update():
    """Trigger a refresh of the triage queue for all connected staff."""
    logger.info("Broadcasting 'queue:update'")
    socketio.emit("queue:update", {"refresh": True}, broadcast=True)

def notify_doctor_update(doctor_data: dict):
    """Update doctor load information in real-time."""
    logger.info("Broadcasting 'doctor:update' for %s", doctor_data.get("id"))
    socketio.emit("doctor:update", doctor_data, broadcast=True)

@socketio.on("connect")
def handle_connect():
    logger.debug("Client connected to WebSocket")

@socketio.on("disconnect")
def handle_disconnect():
    logger.debug("Client disconnected from WebSocket")
