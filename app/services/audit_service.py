"""
Kyro — Audit Service

Provides a unified interface for recording system-wide events, 
from clinical triage outcomes to authentication changes.
"""

from typing import Any, Dict, List, Optional
from app.db.supabase_manager import insert_row, select_rows
from app.core.logging import get_logger

logger = get_logger("services.audit")

TABLE = "audit_log"

class AuditAction:
    # Auth Events
    LOGIN = "LOGIN"
    SIGNUP = "SIGNUP"
    LOGOUT = "LOGOUT"
    
    # Clinical Events
    PATIENT_ADMISSION = "PATIENT_ADMISSION"
    TRIAGE_COMPLETED = "TRIAGE_COMPLETED"
    CASE_RESOLVED = "CASE_RESOLVED"
    NOTIFICATION_SENT = "NOTIFICATION_SENT"
    
    # Staff Events
    LOAD_ADJUSTED = "LOAD_ADJUSTED"
    DOCTOR_SYNC = "DOCTOR_SYNC"
    
    # Model Events
    MODEL_RETRAIN_STARTED = "MODEL_RETRAIN_STARTED"
    MODEL_RETRAIN_SUCCESS = "MODEL_RETRAIN_SUCCESS"
    MODEL_RETRAIN_FAILED = "MODEL_RETRAIN_FAILED"

def log_event(
    actor: str,
    action: str,
    resource: str,
    resource_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Persist an event to the immutable audit trail.
    
    Parameters
    ----------
    actor : str
        Email or ID of the user performing the action.
    action : str
        Standardized choice from AuditAction.
    resource : str
        Type of resource impacted (e.g., 'patient', 'user', 'doctor').
    resource_id : str, optional
        UUID of the specific resource.
    metadata : dict, optional
        Contextual data for the event (e.g., severity, IP address).
    """
    payload = {
        "actor": actor,
        "action": action,
        "resource": resource,
        "resource_id": resource_id,
        "metadata": metadata or {}
    }
    
    try:
        record = insert_row(TABLE, payload)
        logger.info("Audit logged: %s by %s on %s", action, actor, resource)
        return record
    except Exception as exc:
        # We don't want audit failures to crash the main request
        logger.error("Failed to write audit log: %s", exc)
        return {"error": str(exc)}

def list_audit_logs(
    action: Optional[str] = None,
    actor: Optional[str] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Retrieve audit logs with optional filters.
    """
    filters = {}
    if action:
        filters["action"] = action
    if actor:
        filters["actor"] = actor
        
    return select_rows(TABLE, filters=filters, order_by="-created_at", limit=limit)
