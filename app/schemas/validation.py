"""
Kyro — Request / Response Validation Schemas

Uses marshmallow for strict validation of API payloads.
"""

from __future__ import annotations

from marshmallow import Schema, fields, validate, EXCLUDE


# ------------------------------------------------------------------
# Patient
# ------------------------------------------------------------------

class VitalsSchema(Schema):
    """Vital-sign sub-object (NHAMCS-aligned)."""
    heart_rate = fields.Float(required=True)
    systolic_bp = fields.Float(required=True)
    diastolic_bp = fields.Float(required=True)
    temperature = fields.Float(required=True)
    respiratory_rate = fields.Float(load_default=16.0)
    pain_scale = fields.Float(load_default=0.0)
    oxygen_saturation = fields.Float(load_default=98.0)


class PatientIntakeSchema(Schema):
    """Validates POST /api/patients/intake."""
    class Meta:
        unknown = EXCLUDE

    name = fields.String(required=True, validate=validate.Length(min=1, max=200))
    age = fields.Integer(required=True, validate=validate.Range(min=0, max=150))
    gender = fields.String(
        required=True,
        validate=validate.OneOf(["male", "female", "other"]),
    )
    symptoms = fields.List(fields.Dict(), load_default=[])
    vitals = fields.Nested(VitalsSchema, required=True)
    history = fields.Dict(load_default={})
    immediate_triage = fields.Integer(load_default=0, validate=validate.OneOf([0, 1]))
    arrival_by_ems = fields.Integer(load_default=0, validate=validate.OneOf([0, 1]))


class PatientResponseSchema(Schema):
    """Serialises a patient record for API output."""
    id = fields.String()
    name = fields.String()
    age = fields.Integer()
    gender = fields.String()
    symptoms = fields.List(fields.Dict())
    vitals = fields.Dict()
    history = fields.Dict()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()


# ------------------------------------------------------------------
# Doctor
# ------------------------------------------------------------------

class DoctorCreateSchema(Schema):
    """Validates POST /api/doctors."""
    class Meta:
        unknown = EXCLUDE

    name = fields.String(required=True, validate=validate.Length(min=1, max=200))
    specialization = fields.String(required=True, validate=validate.Length(min=1, max=100))
    max_capacity = fields.Integer(load_default=10, validate=validate.Range(min=1))
    is_available = fields.Boolean(load_default=True)


class DoctorResponseSchema(Schema):
    id = fields.String()
    name = fields.String()
    specialization = fields.String()
    max_capacity = fields.Integer()
    current_load = fields.Integer()
    is_available = fields.Boolean()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()


# ------------------------------------------------------------------
# Triage
# ------------------------------------------------------------------

class TriageResponseSchema(Schema):
    id = fields.String()
    patient_id = fields.String()
    severity_level = fields.Integer()
    severity_label = fields.String()
    confidence_score = fields.Float()
    shap_summary = fields.Dict()
    assigned_doctor_id = fields.String(allow_none=True)
    model_version = fields.String()
    created_at = fields.DateTime()


# ------------------------------------------------------------------
# Queue
# ------------------------------------------------------------------

class QueueItemSchema(Schema):
    patient_id = fields.String()
    patient_name = fields.String()
    severity_level = fields.Integer()
    severity_label = fields.String()
    confidence_score = fields.Float()
    assigned_doctor = fields.String(allow_none=True)
    created_at = fields.DateTime()
