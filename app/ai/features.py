"""
Kyro — Emergency Feature Engineering (NHAMCS-aligned)

Transforms raw patient intake data into a feature vector
optimized for emergency severity prediction.

Features:
  Demographics:  age, gender
  Vitals:        temperature, heart_rate, respiratory_rate,
                 systolic_bp, diastolic_bp, pain_scale
  Triage:        immediate_triage, arrival_by_ems
  Chronic:       12 binary condition flags
  Engineered:    shock_index, MAP, tachycardia_flag,
                 hypotension_flag, fever_flag, high_pain_flag,
                 chronic_burden_score
"""

from __future__ import annotations

from typing import Any, Dict, List

import numpy as np
import pandas as pd

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("ai.features")

# ----------------------------------------------------------------
# Chronic condition columns (match NHAMCS fields)
# ----------------------------------------------------------------
CHRONIC_CONDITION_COLS: List[str] = [
    "asthma", "cancer", "ckd", "copd", "chf", "cad",
    "diabetes_type1", "diabetes_type2", "esrd", "htn", "obesity", "osa",
]

# ----------------------------------------------------------------
# All feature columns in model-training order
# ----------------------------------------------------------------
RAW_FEATURES: List[str] = [
    # Demographics
    "age", "gender",
    # Vitals
    "temperature", "heart_rate", "respiratory_rate",
    "systolic_bp", "diastolic_bp", "pain_scale",
    # Triage indicators
    "immediate_triage", "arrival_by_ems",
    # Chronic conditions (binary)
    *CHRONIC_CONDITION_COLS,
]

ENGINEERED_FEATURES: List[str] = [
    "shock_index",
    "mean_arterial_pressure",
    "tachycardia_flag",
    "hypotension_flag",
    "fever_flag",
    "high_pain_flag",
    "chronic_burden_score",
]

ALL_FEATURES: List[str] = RAW_FEATURES + ENGINEERED_FEATURES


def get_feature_names() -> List[str]:
    """Return the ordered feature column names used by the model."""
    return ALL_FEATURES


# ----------------------------------------------------------------
# Feature Engineering Functions
# ----------------------------------------------------------------

def compute_engineered_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add derived clinical features to a DataFrame in-place.

    Expects columns: heart_rate, systolic_bp, diastolic_bp,
                     temperature, pain_scale, and all CHRONIC_CONDITION_COLS.
    """
    # Shock Index = HR / SBP  (normal ~0.5–0.7; >1.0 = concern; >1.3 = critical)
    df["shock_index"] = np.where(
        df["systolic_bp"] > 0,
        df["heart_rate"] / df["systolic_bp"],
        0.0,
    )

    # Mean Arterial Pressure = (2*DBP + SBP) / 3
    df["mean_arterial_pressure"] = (2 * df["diastolic_bp"] + df["systolic_bp"]) / 3

    # Binary instability flags
    df["tachycardia_flag"] = (df["heart_rate"] > 100).astype(int)
    df["hypotension_flag"] = (df["systolic_bp"] < 90).astype(int)
    df["fever_flag"] = (df["temperature"] > 100.4).astype(int)
    df["high_pain_flag"] = (df["pain_scale"] >= 8).astype(int)

    # Chronic burden score = sum of all chronic condition binary flags
    chronic_cols_present = [c for c in CHRONIC_CONDITION_COLS if c in df.columns]
    df["chronic_burden_score"] = df[chronic_cols_present].sum(axis=1)

    return df


# ----------------------------------------------------------------
# API-facing: build vector from patient intake payload
# ----------------------------------------------------------------

def _extract_chronic_flags(history: Dict[str, Any]) -> Dict[str, int]:
    """Extract binary chronic condition flags from patient history."""
    conditions = history.get("chronic_conditions", [])
    if isinstance(conditions, list):
        conditions_lower = {str(c).lower() for c in conditions}
    else:
        conditions_lower = set()

    mapping = {
        "asthma": {"asthma"},
        "cancer": {"cancer"},
        "ckd": {"ckd", "chronic_kidney_disease", "kidney_disease"},
        "copd": {"copd"},
        "chf": {"chf", "congestive_heart_failure", "heart_failure"},
        "cad": {"cad", "coronary_artery_disease", "heart_disease"},
        "diabetes_type1": {"diabetes_type1", "diabtyp1", "type1_diabetes"},
        "diabetes_type2": {"diabetes_type2", "diabtyp2", "type2_diabetes", "diabetes"},
        "esrd": {"esrd", "end_stage_renal"},
        "htn": {"htn", "hypertension"},
        "obesity": {"obesity"},
        "osa": {"osa", "obstructive_sleep_apnea", "sleep_apnea"},
    }

    flags: Dict[str, int] = {}
    for col, aliases in mapping.items():
        flags[col] = 1 if conditions_lower & aliases else 0
    return flags


def build_feature_vector(patient_data: Dict[str, Any]) -> pd.DataFrame:
    """
    Convert a single patient intake dict into a one-row DataFrame
    with the full feature set expected by the model.

    Parameters
    ----------
    patient_data : dict
        Keys: age, gender, vitals, symptoms, history.
        vitals must contain: temperature, heart_rate, respiratory_rate,
                             systolic_bp, diastolic_bp, pain_scale.

    Returns
    -------
    pd.DataFrame with one row, columns = ALL_FEATURES.
    """
    vitals = patient_data.get("vitals", {})
    history = patient_data.get("history", {})

    # Gender encoding: male=1, female=0, other=0
    gender_raw = str(patient_data.get("gender", "other")).lower()
    gender = 1 if gender_raw == "male" else 0

    features: Dict[str, Any] = {
        # Demographics
        "age": patient_data.get("age", 0),
        "gender": gender,
        # Vitals
        "temperature": vitals.get("temperature", 98.6),
        "heart_rate": vitals.get("heart_rate", 80.0),
        "respiratory_rate": vitals.get("respiratory_rate", 16.0),
        "systolic_bp": vitals.get("systolic_bp", 120.0),
        "diastolic_bp": vitals.get("diastolic_bp", 80.0),
        "pain_scale": vitals.get("pain_scale", 0),
        # Triage indicators
        "immediate_triage": int(patient_data.get("immediate_triage", 0)),
        "arrival_by_ems": int(patient_data.get("arrival_by_ems", 0)),
    }

    # Chronic conditions
    features.update(_extract_chronic_flags(history))

    df = pd.DataFrame([features])
    df = compute_engineered_features(df)

    # Ensure column order matches training
    df = df[ALL_FEATURES]

    logger.debug("Feature vector built: %s", {k: features[k] for k in list(features)[:6]})
    return df
