"""
Kyro — Queue Service

Provides a prioritised patient queue view.
"""

from __future__ import annotations

from typing import Any, Dict, List

from app.core.config import settings
from app.core.logging import get_logger
from app.core.cache import get_json, set_json
from app.db.supabase_manager import select_rows

logger = get_logger("services.queue")


def get_queue() -> List[Dict[str, Any]]:
    """
    Return the current triage queue ordered by severity (desc) then time.

    Joins triage_logs with patients to build a human-readable queue.
    """
    cache_key = "queue:current"
    cached = get_json(cache_key)
    if cached:
        return cached

    logs = select_rows(
        "triage_logs",
        columns="id, patient_id, severity_level, confidence_score, assigned_doctor_id, created_at",
        order_by="-severity_level",
    )

    # Enrich with patient name (batch lookup)
    patient_ids = list({log["patient_id"] for log in logs})
    patients_map: Dict[str, str] = {}
    if patient_ids:
        patients = select_rows("patients", columns="id, name")
        patients_map = {p["id"]: p["name"] for p in patients}

    # Enrich with doctor name
    doctor_ids = list({log["assigned_doctor_id"] for log in logs if log.get("assigned_doctor_id")})
    doctors_map: Dict[str, str] = {}
    if doctor_ids:
        doctors = select_rows("doctors", columns="id, name")
        doctors_map = {d["id"]: d["name"] for d in doctors}

    queue: List[Dict[str, Any]] = []
    for log in logs:
        queue.append({
            "patient_id": log["patient_id"],
            "patient_name": patients_map.get(log["patient_id"], "Unknown"),
            "severity_level": log["severity_level"],
            "severity_label": settings.ai.SEVERITY_CLASSES.get(log["severity_level"], "Unknown"),
            "confidence_score": log["confidence_score"],
            "assigned_doctor": doctors_map.get(log.get("assigned_doctor_id", ""), None),
            "created_at": log["created_at"],
        })

    logger.info("Queue fetched: %d items", len(queue))
    
    # Store in cache
    set_json(cache_key, queue, ttl=60) # Short TTL as fallback, will be invalidated explicitly
    
    return queue


# --- Future Phase Hooks ---

def subscribe_queue_updates():
    """Placeholder: WebSocket / Supabase Realtime subscription for live queue."""
    # TODO: Integrate Supabase Realtime or Flask-SocketIO
    raise NotImplementedError("Real-time queue not yet implemented")
