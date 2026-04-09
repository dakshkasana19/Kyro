"""
Kyro — Doctor Service

CRUD operations and availability management for doctors.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.db.supabase_manager import insert_row, select_by_id, select_rows, update_row
from app.core.errors import NotFoundError, AssignmentError
from app.core.logging import get_logger
from app.core.cache import get_json, set_json, delete
from app.core.sockets import notify_doctor_update

logger = get_logger("services.doctor")

TABLE = "doctors"


def create_doctor(data: Dict[str, Any]) -> Dict[str, Any]:
    """Register a new doctor."""
    payload = {
        "name": data["name"],
        "specialization": data["specialization"],
        "max_capacity": data.get("max_capacity", 10),
        "current_load": 0,
        "is_available": data.get("is_available", True),
    }
    doctor = insert_row(TABLE, payload)
    logger.info("Doctor created: id=%s name=%s spec=%s",
                doctor["id"], doctor["name"], doctor["specialization"])
    
    # Invalidate list cache
    delete("doctor:list")
    
    return doctor


def get_doctor(doctor_id: str) -> Dict[str, Any]:
    """Fetch a single doctor or raise NotFoundError."""
    doctor = select_by_id(TABLE, doctor_id)
    if doctor is None:
        raise NotFoundError(f"Doctor not found: {doctor_id}")
    return doctor


def list_doctors(available_only: bool = False) -> List[Dict[str, Any]]:
    """Return all doctors, optionally filtering to available only."""
    cache_key = f"doctor:list:{available_only}"
    cached = get_json(cache_key)
    if cached:
        return cached

    filters = {"is_available": True} if available_only else None
    doctors = select_rows(TABLE, filters=filters, order_by="current_load")
    
    # Store in cache
    set_json(cache_key, doctors, ttl=300)
    
    return doctors


def increment_load(doctor_id: str) -> Dict[str, Any]:
    """
    Increment a doctor's current_load by 1.
    If load reaches max_capacity, mark unavailable.
    """
    doctor = get_doctor(doctor_id)
    new_load = doctor["current_load"] + 1
    updates: Dict[str, Any] = {"current_load": new_load}
    if new_load >= doctor["max_capacity"]:
        updates["is_available"] = False
        logger.warning("Doctor %s reached max capacity (%d)", doctor_id, doctor["max_capacity"])
    
    updated_doctor = update_row(TABLE, doctor_id, updates)
    
    # Invalidate list caches (both versions)
    delete("doctor:list:True")
    delete("doctor:list:False")

    # Notify live clients
    notify_doctor_update(updated_doctor)
    
    return updated_doctor


def decrement_load(doctor_id: str) -> Dict[str, Any]:
    """
    Decrement a doctor's current_load by 1.
    If load was at max, mark available again.
    """
    doctor = get_doctor(doctor_id)
    new_load = max(0, doctor["current_load"] - 1)
    updates: Dict[str, Any] = {"current_load": new_load}
    
    # If they were unavailable but now have space, make them available
    if new_load < doctor["max_capacity"]:
        updates["is_available"] = True
    
    updated_doctor = update_row(TABLE, doctor_id, updates)
    
    # Invalidate caches
    delete("doctor:list:True")
    delete("doctor:list:False")
    notify_doctor_update(updated_doctor)
    
    return updated_doctor


def get_available_specialist(specialization: str | None = None) -> Optional[Dict[str, Any]]:
    """
    Return the available doctor with the lowest load.
    If specialization is provided, filter by it.
    """
    doctors = list_doctors(available_only=True)
    if specialization:
        doctors = [d for d in doctors if d["specialization"].lower() == specialization.lower()]
    if not doctors:
        return None
    # already sorted by current_load ascending
    return doctors[0]


def get_doctor_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Fetch a doctor record by their registration email."""
    # We'll assume the 'name' or a new 'email' column matches. 
    # For now, let's look for a doctor where name matches the prefix or an exact email if we add it.
    # To be safe and professional, I'll add logic to search by a 'email' field.
    doctors = select_rows(TABLE, filters={"email": email})
    return doctors[0] if doctors else None


def list_assigned_patients(doctor_id: str) -> List[Dict[str, Any]]:
    """
    Return all active triage logs assigned to this doctor.
    Enriched with patient details.
    """
    # Use select_rows with a join-like logic (manual enrichment for now as per project pattern)
    # We filter for resolved=False (or missing)
    logs = select_rows("triage_logs", filters={"assigned_doctor_id": doctor_id}, order_by="-created_at")
    
    # In a real DB we'd filter by resolved=False. Since we don't have the column yet, 
    # we'll implement the logic here and I'll add the column in the next step.
    active_logs = [log for log in logs if not log.get("resolved", False)]
    
    if not active_logs:
        return []

    # Batch fetch patient names
    patients = select_rows("patients") 
    patients_map = {p["id"]: p for p in patients}

    enriched = []
    for log in active_logs:
        patient = patients_map.get(log["patient_id"])
        if not patient: continue
        
        enriched.append({
            "triage_id": log["id"],
            "patient_id": patient["id"],
            "patient_name": patient["name"],
            "age": patient["age"],
            "gender": patient["gender"],
            "severity_level": log["severity_level"],
            "severity_label": settings.ai.SEVERITY_CLASSES.get(log["severity_level"], "Unknown"),
            "confidence_score": log["confidence_score"],
            "created_at": log["created_at"],
            "vitals": patient.get("vitals"),
            "symptoms": patient.get("symptoms"),
            "shap_summary": log.get("shap_summary")
        })
    
    return enriched
