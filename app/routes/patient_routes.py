"""
Kyro — Patient API Routes

POST  /api/patients/intake  — Create patient + run triage
GET   /api/patients/<id>    — Get patient by ID
GET   /api/patients         — List recent patients
"""

from __future__ import annotations

from app.core.auth import token_required
from flask import Blueprint, request, g

logger = get_logger("routes.patients")
from app.schemas.validation import PatientIntakeSchema, PatientResponseSchema
from app.services.patient_service import create_patient, get_patient, list_patients
from app.services.triage_service import run_triage
from app.utils.helpers import build_response

logger = get_logger("routes.patients")

patient_bp = Blueprint("patients", __name__, url_prefix="/api/patients")

_intake_schema = PatientIntakeSchema()
_response_schema = PatientResponseSchema()


@patient_bp.route("/intake", methods=["POST"])
def intake():
    """Create a new patient, run AI triage, and assign a doctor."""
    json_data = request.get_json(silent=True)
    if not json_data:
        raise ValidationError("Request body must be valid JSON.")

    # Validate
    errors = _intake_schema.validate(json_data)
    if errors:
        raise ValidationError("Invalid intake data.", details=errors)

    validated = _intake_schema.load(json_data)

    # Persist patient - use hospital_id from token if available, else from payload
    # This allows both public intake (with hospital_id in payload) and staff-entered intake
    target_hospital_id = getattr(g, "hospital_id", json_data.get("hospital_id", "f47ac10b-58cc-4372-a567-0e02b2c3d479"))
    
    patient = create_patient(target_hospital_id, validated)
    logger.info("Intake received for patient %s", patient["id"])

    # Run triage pipeline (predict → explain → assign → log)
    triage_result = run_triage(target_hospital_id, patient["id"], validated)

    return build_response(
        data={
            "patient": patient,
            "triage": triage_result,
        },
        message="Patient intake processed and triage completed.",
        status=201,
    )


@patient_bp.route("/<patient_id>", methods=["GET"])
def get_single_patient(patient_id: str):
    """Retrieve a patient by UUID."""
    patient = get_patient(patient_id)
    return build_response(data=patient)


@patient_bp.route("", methods=["GET"])
@token_required
def get_all_patients():
    """List recent patients for the current hospital."""
    limit = request.args.get("limit", 50, type=int)
    patients = list_patients(g.hospital_id, limit=limit)
    return build_response(data=patients)
