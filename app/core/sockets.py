from app.core.realtime import event_bus
from app.core.logging import get_logger

logger = get_logger("core.sockets")

def notify_new_patient(hospital_id: str, patient_data: dict):
    """Broadcast a global alert via SSE when a new patient enters the system."""
    logger.info("Publishing 'patient:new' for hospital %s: %s", hospital_id, patient_data.get("name"))
    event_bus.publish(hospital_id, "patient:new", patient_data)

def notify_queue_update(hospital_id: str):
    """Trigger a refresh of the triage queue via SSE for all connected staff."""
    logger.info("Publishing 'queue:update' for hospital %s", hospital_id)
    event_bus.publish(hospital_id, "queue:update", {"refresh": True})

def notify_doctor_update(hospital_id: str, doctor_data: dict):
    """Update doctor load information via SSE in real-time."""
    logger.info("Publishing 'doctor:update' for hospital %s: %s", hospital_id, doctor_data.get("id"))
    event_bus.publish(hospital_id, "doctor:update", doctor_data)

# SocketIO logic kept for backward compatibility but effectively silenced for SSE
from flask_socketio import SocketIO
socketio = SocketIO(cors_allowed_origins="*", async_mode="threading")

@socketio.on("connect")
def handle_connect():
    logger.debug("Client connected to WebSocket (Deprecated)")

@socketio.on("disconnect")
def handle_disconnect():
    logger.debug("Client disconnected from WebSocket (Deprecated)")
