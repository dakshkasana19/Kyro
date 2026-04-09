"""
Kyro — AI Inference Pipeline (Emergency-Optimized)

Loads the trained XGBoost model and provides:
  • predict_severity()  — severity class + confidence
  • explain_prediction() — SHAP feature importance
"""

from __future__ import annotations

import os
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Tuple

import numpy as np
import pandas as pd
import shap
from xgboost import XGBClassifier

from app.ai.features import build_feature_vector, get_feature_names, ALL_FEATURES
from app.core.config import settings
from app.core.errors import AIModelError
from app.core.logging import get_logger
from app.core.cache import get_json, set_json

logger = get_logger("ai.inference")

# Module-level cache
_model: XGBClassifier | None = None
_explainer: shap.TreeExplainer | None = None


def _load_model() -> XGBClassifier:
    """Load XGBoost model from disk (cached)."""
    global _model
    if _model is not None:
        return _model

    model_path = settings.ai.MODEL_PATH
    if not Path(model_path).exists():
        raise AIModelError(
            f"Model file not found at '{model_path}'. "
            "Run `python -m app.ai.train` first."
        )

    _model = XGBClassifier()
    _model.load_model(model_path)
    logger.info("XGBoost model loaded from %s (features: %d)", model_path, len(ALL_FEATURES))
    return _model


def _get_explainer() -> shap.TreeExplainer:
    """Return a SHAP TreeExplainer (cached)."""
    global _explainer
    if _explainer is None:
        _explainer = shap.TreeExplainer(_load_model())
        logger.info("SHAP TreeExplainer initialised")
    return _explainer


def _get_cache_key(prefix: str, patient_data: Dict[str, Any]) -> str:
    """
    Generate a stable cache key based on critical patient attributes.
    Focuses on vitals and symptoms as requested.
    """
    # Extract only the critical features
    vitals = patient_data.get("vitals", {})
    symptoms = patient_data.get("symptoms", [])
    
    # Sort symptoms list for consistency
    sorted_symptoms = sorted(symptoms) if isinstance(symptoms, list) else symptoms
    
    # Create a stable payload
    payload = {
        "vitals": vitals,
        "symptoms": sorted_symptoms,
        "age": patient_data.get("age"),
        "gender": patient_data.get("gender")
    }
    
    # MD5 hash for a compact, stable key
    payload_str = json.dumps(payload, sort_keys=True)
    payload_hash = hashlib.md5(payload_str.encode()).hexdigest()
    
    return f"{prefix}:{payload_hash}"


def predict_severity(patient_data: Dict[str, Any]) -> Tuple[int, float, np.ndarray]:
    """
    Predict severity for a single patient.

    Parameters
    ----------
    patient_data : dict
        Raw patient intake dict (age, gender, vitals, history, etc.).

    Returns
    -------
    (severity_level, confidence_score, probabilities)
    """
    cache_key = _get_cache_key("prediction", patient_data)
    cached = get_json(cache_key)
    if cached:
        logger.info("Cache HIT [AI Prediction] for patient data")
        # Redis-JSON returns lists, convert probabilities back to numpy if needed
        return cached["severity"], cached["confidence"], np.array(cached["proba"])

    try:
        model = _load_model()
        X = build_feature_vector(patient_data)
        proba = model.predict_proba(X)[0]  # shape (4,)
        severity = int(np.argmax(proba))
        confidence = float(proba[severity])

        logger.info(
            "Prediction: severity=%d (%s)  confidence=%.3f  proba=%s",
            severity,
            settings.ai.SEVERITY_CLASSES.get(severity, "Unknown"),
            confidence,
            proba.round(3).tolist(),
        )
        
        # Cache the result
        set_json(cache_key, {
            "severity": severity,
            "confidence": confidence,
            "proba": proba.tolist()
        }, ttl=settings.redis.DEFAULT_TTL)
        
        return severity, confidence, proba
    except AIModelError:
        raise
    except Exception as exc:
        logger.exception("Severity prediction failed")
        raise AIModelError(f"Prediction failed: {exc}") from exc


def explain_prediction(patient_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate SHAP explanation for a single patient prediction.

    Returns
    -------
    dict with keys: predicted_class, predicted_label,
                    feature_importance (sorted by |shap_value|),
                    risk_factors (top contributing features).
    """
    cache_key = _get_cache_key("explanation", patient_data)
    cached = get_json(cache_key)
    if cached:
        logger.info("Cache HIT [AI Explanation] for patient data")
        return cached

    try:
        explainer = _get_explainer()
        X = build_feature_vector(patient_data)
        shap_values = explainer.shap_values(X)

        severity, confidence, _ = predict_severity(patient_data)
        feature_names = get_feature_names()

        # SHAP values format varies by version:
        # - shap <0.45: list of 2D arrays, one per class
        # - shap >=0.45: single 3D array (n_samples, n_features, n_classes)
        if isinstance(shap_values, list):
            class_shap = shap_values[severity][0]
        elif shap_values.ndim == 3:
            class_shap = shap_values[0, :, severity]
        else:
            class_shap = shap_values[0]

        importance = sorted(
            zip(feature_names, class_shap.tolist()),
            key=lambda x: abs(x[1]),
            reverse=True,
        )

        # Identify top risk factors (positive SHAP = pushes toward this class)
        risk_factors = [
            {"feature": f, "shap_value": round(v, 4), "direction": "risk" if v > 0 else "protective"}
            for f, v in importance[:10]
        ]

        summary = {
            "predicted_class": severity,
            "predicted_label": settings.ai.SEVERITY_CLASSES.get(severity, "Unknown"),
            "confidence": round(confidence, 4),
            "feature_importance": [
                {"feature": f, "shap_value": round(v, 4)} for f, v in importance
            ],
            "risk_factors": risk_factors,
        }
        
        # Cache the result
        set_json(cache_key, summary, ttl=settings.redis.DEFAULT_TTL)
        
        logger.debug("SHAP explanation generated for severity=%d", severity)
        return summary
    except AIModelError:
        raise
    except Exception as exc:
        logger.exception("SHAP explanation failed")
        raise AIModelError(f"Explanation failed: {exc}") from exc


def reload_model() -> None:
    """Force-reload the model from disk (useful after retraining)."""
    global _model, _explainer
    _model = None
    _explainer = None
    _load_model()
    logger.info("Model reloaded from disk")
    _load_model()
    logger.info("Model reloaded from disk")
