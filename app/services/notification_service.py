"""
Kyro — Clinical Notification Service

Handles all patient-related alerts across multiple channels:
  1. Real-time WebSockets (Immediate UI feedback)
  2. Mocked SMS (Mock external integration)
  3. Mocked Email (Mock external integration)
"""

from typing import Any, Dict
from app.core.sockets import notify_new_patient, event_bus
from app.services.audit_service import log_event, AuditAction
from app.core.logging import get_logger

logger = get_logger("services.notifications")

def process_admission_notifications(hospital_id: str, patient_name: str, triage_results: Dict[str, Any]):
    """
    Determine and dispatch appropriate notifications based on severity and hospital scope.
    """
    severity_level = triage_results.get("severity_level", 1)
    patient_id = triage_results.get("patient_id")
    
    # 1. Scoped Real-time Notification via SSE
    notify_new_patient(hospital_id, {
        "name": patient_name,
        "severity_level": severity_level,
        "patient_id": patient_id
    })
    
    # 2. Critical Path (Level 3)
    if severity_level == 3:
        _trigger_critical_alerts(hospital_id, patient_name, patient_id)
    else:
        logger.info("Notification: Standard admission [Hospital=%s, Patient=%s, Level=%d]", 
                    hospital_id, patient_id, severity_level)

def _trigger_critical_alerts(hospital_id: str, name: str, patient_id: str):
    """
    High-intensity alerts for life-threatening cases, scoped by hospital.
    """
    # A. Scoped Critical SSE Alert
    event_bus.publish(hospital_id, "critical:alert", {
        "name": name,
        "patient_id": patient_id,
        "message": "Immediate Medical Intervention Required"
    })
    
    # B. MOCKED SMS (Console Stub)
    logger.warning(">>> [MOCKED SMS] Sent to ER Lead | Hospital: %s | Msg: CRITICAL ADMISSION: %s (ID: %s)", 
                   hospital_id, name, patient_id)
    
    # C. MOCKED EMAIL (Console Stub)
    logger.warning(">>> [MOCKED EMAIL] Sent to intake@hospital-%s.com | Subject: ALERT: Level 3 Triage - %s", 
                   hospital_id, name)
    
    # D. Audit Entry
    log_event(
        actor="SYSTEM",
        action=AuditAction.NOTIFICATION_SENT,
        resource="patient",
        resource_id=patient_id,
        metadata={
            "hospital_id": hospital_id,
            "channels": ["sse_stream", "sms_mock", "email_mock"],
            "type": "CRITICAL_ALERT"
        }
    )
    
    logger.info("Notification: Critical alert dispatched [Patient=%s]", patient_id)
