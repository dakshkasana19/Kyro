"""
Kyro — Patient Service

Business logic for patient intake and retrieval.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.db.supabase_manager import insert_row, select_by_id, select_rows
from app.core.errors import NotFoundError, ValidationError
from app.core.logging import get_logger
from app.core.sockets import notify_new_patient

logger = get_logger("services.patient")

TABLE = "patients"


def create_patient(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Persist a new patient record from validated intake data.

    Returns the created patient row.
    """
    payload = {
        "name": data["name"],
        "age": data["age"],
        "gender": data["gender"],
        "symptoms": data["symptoms"],
        "vitals": data["vitals"],
        "history": data.get("history", {}),
    }
    patient = insert_row(TABLE, payload)
    logger.info("Patient created: id=%s name=%s", patient["id"], patient["name"])
    
    # Notify live clients
    notify_new_patient(patient)
    
    return patient


def get_patient(patient_id: str) -> Dict[str, Any]:
    """Fetch a single patient by id or raise NotFoundError."""
    patient = select_by_id(TABLE, patient_id)
    if patient is None:
        raise NotFoundError(f"Patient not found: {patient_id}")
    return patient


def list_patients(limit: int = 50) -> List[Dict[str, Any]]:
    """Return recent patients, ordered by creation date descending."""
    return select_rows(TABLE, order_by="-created_at", limit=limit)
