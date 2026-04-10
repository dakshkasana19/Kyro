"""
Kyro — Standalone Flask API Server

Lightweight server for testing AI triage predictions.
No Supabase required — uses the trained XGBoost model directly.

Usage:
    python server.py

Endpoints:
    POST /api/patients/intake     — Full patient intake + triage
    GET  /api/health              — Health check
    POST /api/predict             — Predict severity for a patient
    POST /api/explain             — Predict + SHAP explanation
    POST /api/batch-predict       — Predict for multiple patients
    GET  /api/model/info          — Model metadata + feature list
"""

from __future__ import annotations

import json
import traceback
from pathlib import Path

from flask import Flask, jsonify, request

# ── AI imports ──────────────────────────────────────────────────
from app.ai.inference import predict_severity, explain_prediction, reload_model
from app.ai.features import ALL_FEATURES, CHRONIC_CONDITION_COLS
from app.core.config import settings
from app.core.logging import setup_logging
from flask_cors import CORS

setup_logging()

app = Flask(__name__)
app.config["SECRET_KEY"] = settings.flask.SECRET_KEY
CORS(app)  # Allow cross-origin requests from the Next.js frontend

# ── Register Multi-Tenant Blueprints ────────────────────────────
from app.routes.auth_routes import auth_bp
from app.routes.patient_routes import patient_bp
from app.routes.doctor_routes import doctor_bp
from app.routes.queue_routes import queue_bp
from app.routes.health_routes import health_bp
from app.routes.audit_routes import audit_bp
from app.routes.model_routes import model_bp
from app.routes.realtime_routes import realtime_bp

app.register_blueprint(auth_bp)
app.register_blueprint(patient_bp)
app.register_blueprint(doctor_bp)
app.register_blueprint(queue_bp)
app.register_blueprint(health_bp)
app.register_blueprint(audit_bp)
app.register_blueprint(model_bp)
app.register_blueprint(realtime_bp)

# Severity label map
SEVERITY_LABELS = {0: "Low", 1: "Medium", 2: "High", 3: "Critical"}


# ────────────────────────────────────────────────────────────────
# POST /api/patients/intake — Full intake (matches original API)
# ────────────────────────────────────────────────────────────────
@app.route("/api/patients/intake", methods=["POST"])
def patient_intake():
    """
    Full patient intake — accepts the same payload as the production API,
    runs AI triage, and returns severity + explanation.

    No Supabase needed. Patients are not persisted.

    Request body:
    {
        "name": "Ramesh Kumar",
        "age": 72,
        "gender": "Male",
        "symptoms": { ... },
        "vitals": {
            "heart_rate": 155,
            "systolic_bp": 78,
            "diastolic_bp": 45,
            "oxygen_saturation": 88,
            "temperature": 101.2,
            "respiratory_rate": 32,
            "pain_scale": 9
        },
        "history": {
            "conditions": ["chf", "cad", "htn", "diabetes_type2"]
        }
    }
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be valid JSON."}), 400

    # Normalize: history.conditions → history.chronic_conditions
    history = data.get("history", {})
    if "conditions" in history and "chronic_conditions" not in history:
        history["chronic_conditions"] = history.pop("conditions")
        data["history"] = history

    error = _validate_patient(data)
    if error:
        return jsonify({"error": error}), 400

    try:
        import uuid
        patient_id = str(uuid.uuid4())

        severity, confidence, probabilities = predict_severity(data)
        explanation = explain_prediction(data)

        return jsonify({
            "patient": {
                "id": patient_id,
                "name": data.get("name", "Unknown"),
                "age": data.get("age"),
                "gender": data.get("gender"),
                "symptoms": data.get("symptoms"),
                "vitals": data.get("vitals"),
            },
            "triage": {
                "severity": severity,
                "severity_label": SEVERITY_LABELS.get(severity, "Unknown"),
                "confidence": round(confidence, 4),
                "probabilities": {
                    SEVERITY_LABELS[i]: round(float(p), 4)
                    for i, p in enumerate(probabilities)
                },
                "risk_factors": explanation.get("risk_factors", [])[:5],
            },
            "message": "Patient intake processed and triage completed.",
        }), 201
    except Exception as e:
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500


# ────────────────────────────────────────────────────────────────
# Health Check
# ────────────────────────────────────────────────────────────────
@app.route("/api/health", methods=["GET"])
def health():
    model_exists = Path(settings.ai.MODEL_PATH).exists()
    return jsonify({
        "status": "healthy",
        "service": "kyro-triage-ai",
        "model_loaded": model_exists,
        "model_path": settings.ai.MODEL_PATH,
        "features_count": len(ALL_FEATURES),
    })


# ────────────────────────────────────────────────────────────────
# POST /api/predict — Severity prediction
# ────────────────────────────────────────────────────────────────
@app.route("/api/predict", methods=["POST"])
def predict():
    """
    Predict severity for a single patient.

    Request body:
    {
        "age": 72,
        "gender": "male",
        "vitals": {
            "heart_rate": 145,
            "systolic_bp": 72,
            "diastolic_bp": 40,
            "temperature": 103.2,
            "respiratory_rate": 32,
            "pain_scale": 9
        },
        "history": {
            "chronic_conditions": ["chf", "cad", "htn", "diabetes"]
        },
        "immediate_triage": 1,
        "arrival_by_ems": 1
    }
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be valid JSON."}), 400

    # Validate minimum required fields
    error = _validate_patient(data)
    if error:
        return jsonify({"error": error}), 400

    try:
        severity, confidence, probabilities = predict_severity(data)

        return jsonify({
            "severity": severity,
            "severity_label": SEVERITY_LABELS.get(severity, "Unknown"),
            "confidence": round(confidence, 4),
            "probabilities": {
                SEVERITY_LABELS[i]: round(float(p), 4)
                for i, p in enumerate(probabilities)
            },
        })
    except Exception as e:
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500

# ────────────────────────────────────────────────────────────────
# POST /api/explain — Prediction + SHAP explanation
# ────────────────────────────────────────────────────────────────
@app.route("/api/explain", methods=["POST"])
def explain():
    """
    Predict severity AND return SHAP-based feature importance.
    Same request body as /api/predict.
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be valid JSON."}), 400

    error = _validate_patient(data)
    if error:
        return jsonify({"error": error}), 400

    try:
        explanation = explain_prediction(data)
        return jsonify(explanation)
    except Exception as e:
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500


# ────────────────────────────────────────────────────────────────
# POST /api/batch-predict — Multiple patients at once
# ────────────────────────────────────────────────────────────────
@app.route("/api/batch-predict", methods=["POST"])
def batch_predict():
    """
    Predict severity for multiple patients.

    Request body:
    {
        "patients": [ {...patient1...}, {...patient2...} ]
    }
    """
    data = request.get_json(silent=True)
    if not data or "patients" not in data:
        return jsonify({"error": "Request body must contain 'patients' array."}), 400

    patients = data["patients"]
    if not isinstance(patients, list) or len(patients) == 0:
        return jsonify({"error": "'patients' must be a non-empty array."}), 400

    if len(patients) > 100:
        return jsonify({"error": "Maximum 100 patients per batch."}), 400

    results = []
    for i, patient in enumerate(patients):
        try:
            severity, confidence, probabilities = predict_severity(patient)
            results.append({
                "index": i,
                "name": patient.get("name", f"Patient-{i}"),
                "severity": severity,
                "severity_label": SEVERITY_LABELS.get(severity, "Unknown"),
                "confidence": round(confidence, 4),
                "probabilities": {
                    SEVERITY_LABELS[j]: round(float(p), 4)
                    for j, p in enumerate(probabilities)
                },
            })
        except Exception as e:
            results.append({
                "index": i,
                "name": patient.get("name", f"Patient-{i}"),
                "error": str(e),
            })

    return jsonify({
        "total": len(patients),
        "results": results,
        "summary": _summarize_batch(results),
    })


# ────────────────────────────────────────────────────────────────
# GET /api/model/info — Model metadata
# ────────────────────────────────────────────────────────────────
@app.route("/api/model/info", methods=["GET"])
def model_info():
    """Return model metadata and feature configuration."""
    meta_path = Path(settings.ai.MODEL_PATH).parent / "model_meta.json"
    meta = {}
    if meta_path.exists():
        meta = json.loads(meta_path.read_text())

    return jsonify({
        "model_version": settings.ai.MODEL_VERSION,
        "model_path": settings.ai.MODEL_PATH,
        "features": ALL_FEATURES,
        "n_features": len(ALL_FEATURES),
        "chronic_conditions_supported": CHRONIC_CONDITION_COLS,
        "severity_classes": SEVERITY_LABELS,
        "training_metadata": meta,
    })


# ────────────────────────────────────────────────────────────────
# POST /api/model/reload — Force reload model from disk
# ────────────────────────────────────────────────────────────────
@app.route("/api/model/reload", methods=["POST"])
def model_reload():
    """Reload the XGBoost model from disk (after retraining)."""
    try:
        reload_model()
        return jsonify({"message": "Model reloaded successfully."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────
def _validate_patient(data: dict) -> str | None:
    """Basic validation — returns error string or None."""
    if "age" not in data:
        return "Missing required field: 'age'"
    if "vitals" not in data:
        return "Missing required field: 'vitals'"
    vitals = data["vitals"]
    required_vitals = ["heart_rate", "systolic_bp", "diastolic_bp"]
    for v in required_vitals:
        if v not in vitals:
            return f"Missing required vital: '{v}'"
    return None


def _summarize_batch(results: list) -> dict:
    """Summarize batch prediction results."""
    severity_counts = {"Low": 0, "Medium": 0, "High": 0, "Critical": 0, "Error": 0}
    for r in results:
        if "error" in r:
            severity_counts["Error"] += 1
        else:
            label = r.get("severity_label", "Unknown")
            severity_counts[label] = severity_counts.get(label, 0) + 1
    return severity_counts


# ────────────────────────────────────────────────────────────────
# Error Handlers
# ────────────────────────────────────────────────────────────────
from app.core.errors import KyroError

@app.errorhandler(KyroError)
def handle_kyro_error(error):
    return jsonify(error.to_dict()), error.status_code

@app.errorhandler(404)
def not_found(_):
    return jsonify({"error": "Endpoint not found."}), 404


@app.errorhandler(405)
def method_not_allowed(_):
    return jsonify({"error": "HTTP method not allowed."}), 405


@app.errorhandler(500)
def internal_error(e):
    return jsonify({"error": "Internal server error.", "details": str(e)}), 500


# ────────────────────────────────────────────────────────────────
# Main
# ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  KYRO TRIAGE-AI — Unified Flask Server")
    print("=" * 60)
    print(f"  Model:    {settings.ai.MODEL_PATH}")
    print(f"  Features: {len(ALL_FEATURES)}")
    print(f"  Server:   http://localhost:5000")
    print()
    print("  AI Endpoints:")
    print("    POST /api/patients/intake — Full intake + triage")
    print("    POST /api/predict        — Predict severity")
    print("    POST /api/explain        — Predict + SHAP")
    print("    POST /api/batch-predict  — Batch predictions")
    print()
    print("  Clinical Portal:")
    print("    POST /api/v1/auth/login  — Staff login")
    print("    POST /api/v1/auth/signup — Staff signup")
    print("    GET  /api/queue          — Triage queue")
    print("    GET  /api/v1/realtime/stream — SSE stream")
    print("    GET  /api/v1/audit       — Audit logs")
    print("=" * 60)

    app.run(host="0.0.0.0", port=5000, debug=True)
