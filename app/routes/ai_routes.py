"""
Kyro — AI Triage Prediction Routes
Merged from the standalone server.py
"""

import traceback
from flask import Blueprint, jsonify, request
from app.ai.inference import predict_severity, explain_prediction, reload_model
from app.ai.features import ALL_FEATURES, CHRONIC_CONDITION_COLS
from app.core.config import settings

ai_bp = Blueprint("ai", __name__, url_prefix="/api")

SEVERITY_LABELS = {0: "Low", 1: "Medium", 2: "High", 3: "Critical"}

@ai_bp.route("/predict", methods=["POST"])
def predict():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be valid JSON."}), 400
    
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

@ai_bp.route("/explain", methods=["POST"])
def explain():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be valid JSON."}), 400
    
    try:
        explanation = explain_prediction(data)
        return jsonify(explanation)
    except Exception as e:
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500

@ai_bp.route("/batch-predict", methods=["POST"])
def batch_predict():
    data = request.get_json(silent=True)
    if not data or "patients" not in data:
        return jsonify({"error": "Request body must contain 'patients' array."}), 400

    patients = data["patients"]
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
            results.append({ "index": i, "error": str(e) })

    return jsonify({"total": len(patients), "results": results})

@ai_bp.route("/model/info", methods=["GET"])
def model_info():
    return jsonify({
        "model_version": settings.ai.MODEL_VERSION,
        "features": ALL_FEATURES,
        "n_features": len(ALL_FEATURES),
        "severity_classes": SEVERITY_LABELS,
    })
