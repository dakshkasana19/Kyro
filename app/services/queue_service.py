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


def get_queue(hospital_id: str) -> List[Dict[str, Any]]:
    """
    Return the current triage queue for a specific hospital, ordered by severity.
    """
    cache_key = f"queue:{hospital_id}"
    cached = get_json(cache_key)
    if cached:
        return cached

    logs = select_rows(
        "triage_logs",
        columns="id, patient_id, severity_level, confidence_score, assigned_doctor_id, created_at",
        filters={"hospital_id": hospital_id},
        order_by="-severity_level",
    )

    # Enrich with patient name
    patients = select_rows("patients", columns="id, name", filters={"hospital_id": hospital_id})
    patients_map = {p["id"]: p["name"] for p in patients}

    # Enrich with doctor name
    doctors = select_rows("doctors", columns="id, name", filters={"hospital_id": hospital_id})
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

    logger.info("Queue fetched for hospital %s: %d items", hospital_id, len(queue))
    
    # Store in cache
    set_json(cache_key, queue, ttl=300)
    
    return queue


# --- Future Phase Hooks ---

def subscribe_queue_updates():
    """Placeholder: WebSocket / Supabase Realtime subscription for live queue."""
    # TODO: Integrate Supabase Realtime or Flask-SocketIO
    raise NotImplementedError("Real-time queue not yet implemented")
