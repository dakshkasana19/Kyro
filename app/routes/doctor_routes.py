"""
Kyro — Doctor API Routes

POST  /api/doctors     — Register a new doctor
GET   /api/doctors     — List all doctors
GET   /api/doctors/<id> — Get a single doctor
"""

from __future__ import annotations

from flask import Blueprint, request

from app.core.errors import ValidationError
from app.core.logging import get_logger
from app.schemas.validation import DoctorCreateSchema
from app.services.doctor_service import create_doctor, get_doctor, list_doctors
from app.utils.helpers import build_response
from app.core.auth import token_required, require_role

logger = get_logger("routes.doctors")

doctor_bp = Blueprint("doctors", __name__, url_prefix="/api/doctors")

_create_schema = DoctorCreateSchema()


@doctor_bp.route("", methods=["POST"])
@token_required
@require_role(["Admin"])
def register_doctor():
    """Register a new doctor."""
    json_data = request.get_json(silent=True)
    if not json_data:
        raise ValidationError("Request body must be valid JSON.")

    errors = _create_schema.validate(json_data)
    if errors:
        raise ValidationError("Invalid doctor data.", details=errors)

    validated = _create_schema.load(json_data)
    doctor = create_doctor(validated)
    logger.info("Doctor registered: %s", doctor["id"])
    return build_response(data=doctor, message="Doctor registered.", status=201)


@doctor_bp.route("", methods=["GET"])
@token_required
@require_role(["Admin", "Doctor", "Nurse"])
def get_all_doctors():
    """List all doctors. Use ?available=true to filter."""
    available_only = request.args.get("available", "").lower() == "true"
    doctors = list_doctors(available_only=available_only)
    return build_response(data=doctors)


@doctor_bp.route("/<doctor_id>", methods=["GET"])
def get_single_doctor(doctor_id: str):
    """Get a doctor by UUID."""
    doctor = get_doctor(doctor_id)
    return build_response(data=doctor)
