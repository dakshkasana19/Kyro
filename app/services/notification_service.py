"""
Kyro — Clinical Notification Service

Handles all patient-related alerts across multiple channels:
  1. Real-time WebSockets (Immediate UI feedback)
  2. Mocked SMS (Mock external integration)
  3. Mocked Email (Mock external integration)
"""

from typing import Any, Dict
from app.core.sockets import socketio
from app.services.audit_service import log_event, AuditAction
from app.core.logging import get_logger

logger = get_logger("services.notifications")

def process_admission_notifications(patient_name: str, triage_results: Dict[str, Any]):
    """
    Determine and dispatch appropriate notifications based on severity.
    """
    severity_level = triage_results.get("severity_level", 1)
    patient_id = triage_results.get("patient_id")
    
    # 1. Base WebSocket Notification (General Admission)
    socketio.emit("patient:new", {
        "name": patient_name,
        "severity_level": severity_level,
        "patient_id": patient_id
    })
    
    # 2. Critical Path (Level 3)
    if severity_level == 3:
        _trigger_critical_alerts(patient_name, patient_id)
    else:
        logger.info("Notification: Standard admission [Patient=%s, Level=%d]", patient_id, severity_level)

def _trigger_critical_alerts(name: str, patient_id: str):
    """
    High-intensity alerts for life-threatening cases.
    """
    # A. Special WebSocket Alert for persistent UI display
    socketio.emit("critical:alert", {
        "name": name,
        "patient_id": patient_id,
        "message": "Immediate Medical Intervention Required"
    })
    
    # B. MOCKED SMS (Console Stub)
    # In production, replace with Twilio or similar
    logger.warning(">>> [MOCKED SMS] Sent to ER Lead | Msg: CRITICAL ADMISSION: %s (ID: %s)", name, patient_id)
    
    # C. MOCKED EMAIL (Console Stub)
    # In production, replace with Amazon SES or SendGrid
    logger.warning(">>> [MOCKED EMAIL] Sent to intake-team@hospital.com | Subject: ALERT: Level 3 Triage - %s", name)
    
    # D. Audit Entry
    log_event(
        actor="SYSTEM",
        action=AuditAction.NOTIFICATION_SENT,
        resource="patient",
        resource_id=patient_id,
        metadata={
            "channels": ["websocket", "sms_mock", "email_mock"],
            "type": "CRITICAL_ALERT"
        }
    )
    
    logger.info("Notification: Critical alert dispatched [Patient=%s]", patient_id)
