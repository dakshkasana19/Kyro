"""
Kyro — Triage Service

Orchestrates the full triage pipeline:
  1. Run AI severity prediction
  2. Generate SHAP explanation
  3. Assign a doctor
  4. Persist triage log
"""

from __future__ import annotations

from typing import Any, Dict

from app.ai.inference import predict_severity, explain_prediction
from app.core.config import settings
from app.core.errors import AssignmentError
from app.core.logging import get_logger
from app.db.supabase_manager import insert_row, update_row
from app.services.doctor_service import get_available_specialist, increment_load, decrement_load
from app.core.cache import delete
from app.services.audit_service import log_event, AuditAction
from app.services.notification_service import process_admission_notifications

logger = get_logger("services.triage")

TABLE = "triage_logs"


def run_triage(patient_id: str, patient_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute the full triage pipeline for one patient.

    Parameters
    ----------
    patient_id : str
        UUID of the already-persisted patient record.
    patient_data : dict
        The raw intake payload (age, vitals, symptoms, history).

    Returns
    -------
    dict  — The persisted triage_log row.
    """
    # Step 1 — Predict severity
    severity, confidence, _ = predict_severity(patient_data)
    severity_label = settings.ai.SEVERITY_CLASSES.get(severity, "Unknown")
    logger.info("Triage for patient %s → severity=%d (%s) confidence=%.3f",
                patient_id, severity, severity_label, confidence)

    # Step 2 — Explain
    shap_summary = explain_prediction(patient_data)

    # Step 3 — Assign doctor
    assigned_doctor_id = _assign_doctor(severity)

    # Step 4 — Persist triage log
    log_payload = {
        "patient_id": patient_id,
        "severity_level": severity,
        "confidence_score": round(confidence, 4),
        "shap_summary": shap_summary,
        "assigned_doctor_id": assigned_doctor_id,
        "model_version": settings.ai.MODEL_VERSION,
    }
    triage_log = insert_row(TABLE, log_payload)

    # Invalidate queue cache
    delete("queue:current")

    # Notify live clients & channels
    notify_queue_update()
    process_admission_notifications(
        patient_name=patient_data.get("name", "Unknown"),
        triage_results={
            "severity_level": severity,
            "patient_id": patient_id
        }
    )

    # Log Audit
    log_event(
        actor="SYSTEM",
        action=AuditAction.TRIAGE_COMPLETED,
        resource="patient",
        resource_id=patient_id,
        metadata={
            "severity": severity,
            "label": severity_label,
            "confidence": round(confidence, 4)
        }
    )

    # Enrich for response
    triage_log["severity_label"] = severity_label
    return triage_log


def _assign_doctor(severity: int) -> str | None:
    """
    Doctor assignment logic (Phase 2).

    Rules:
    - Critical (3): assign available specialist with lowest load.
    - Others: assign any available doctor with lowest load.

    Returns assigned doctor id or None if no doctor is available.
    """
    if severity == 3:
        # Try specialist first (could be enhanced with symptom-based routing)
        doctor = get_available_specialist()
    else:
        doctor = get_available_specialist()

    if doctor is None:
        logger.warning("No available doctor for severity=%d", severity)
        return None

    increment_load(doctor["id"])
    logger.info("Assigned doctor %s (load→%d) for severity=%d",
                doctor["id"], doctor["current_load"] + 1, severity)
    return doctor["id"]


def resolve_triage_session(log_id: str, actor: str = "SYSTEM") -> Dict[str, Any]:
    """
    Mark a triage log as resolved and decrement the assigned doctor's load.
    """
    from app.db.supabase_manager import select_by_id
    log = select_by_id(TABLE, log_id)
    if not log:
        from app.core.errors import DatabaseError
        raise DatabaseError(f"Triage log not found: {log_id}")
    
    # Mark as resolved
    updated_log = update_row(TABLE, log_id, {"resolved": True})
    
    # Decrement doctor load if one was assigned
    doctor_id = log.get("assigned_doctor_id")
    if doctor_id:
        decrement_load(doctor_id)
        
    # Invalidate cache
    delete("queue:current")
    notify_queue_update()
    
    # Log Audit
    log_event(
        actor=actor,
        action=AuditAction.CASE_RESOLVED,
        resource="triage_log",
        resource_id=log_id,
        metadata={"doctor_id": doctor_id}
    )
    
    return updated_log


def unassign_doctor_patients(doctor_id: str) -> int:
    """
    Mark all un-resolved patients for this doctor as unassigned.
    Used when a doctor is removed from staff.
    """
    from app.db.supabase_manager import select_rows, update_row
    from app.core.cache import delete
    logs = select_rows(TABLE, filters={"assigned_doctor_id": doctor_id, "resolved": False})
    for log in logs:
        update_row(TABLE, log["id"], {"assigned_doctor_id": None})
    
    if logs:
        delete("queue:current")
        notify_queue_update()
        
    return len(logs)


def optimize_assignment() -> None:
    """
    Placeholder for future Linear Programming based assignment
    optimization (e.g., PuLP / OR-Tools).
    """
    # TODO: Implement LP-based doctor assignment optimization
    raise NotImplementedError("LP-based assignment not yet implemented")
