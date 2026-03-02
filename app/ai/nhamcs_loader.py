"""
Kyro — NHAMCS 2022 Data Loader

Supports two loading modes:
  1. Pre-processed dataset (dataset.csv from prep_dataset.py)
  2. Raw NHAMCS 2022 ED file (ed2022.csv)

Existing file locations:
  app/ai/ed2022.csv    — Raw NHAMCS data
  app/ai/dataset.csv   — Pre-processed by prep_dataset.py
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from app.ai.features import (
    CHRONIC_CONDITION_COLS,
    RAW_FEATURES,
    compute_engineered_features,
)
from app.core.logging import get_logger

logger = get_logger("ai.nhamcs_loader")

# Default paths (relative to project root)
DEFAULT_PREPROCESSED_PATH = "app/ai/dataset.csv"
DEFAULT_RAW_NHAMCS_PATH = "app/ai/ed2022.csv"


def load_preprocessed_dataset(filepath: Optional[str] = None) -> pd.DataFrame:
    """
    Load the already-preprocessed dataset.csv (from prep_dataset.py).

    This is the fastest path — the data is already cleaned and
    feature-engineered.

    Returns
    -------
    pd.DataFrame ready for training with all features + severity.
    """
    path = Path(filepath or DEFAULT_PREPROCESSED_PATH)
    if not path.exists():
        raise FileNotFoundError(
            f"Pre-processed dataset not found at '{path}'. "
            f"Either run prep_dataset.py first, or use load_nhamcs_raw()."
        )

    logger.info("Loading pre-processed dataset from %s", path)
    df = pd.read_csv(path, low_memory=False)
    logger.info("Loaded %d rows, %d columns", len(df), len(df.columns))

    # Harmonize column names to match our feature set
    df = _harmonize_columns(df)

    # Recompute engineered features to ensure consistency
    df = compute_engineered_features(df)

    # Rename severity column
    if "severity_class" in df.columns and "severity" not in df.columns:
        df = df.rename(columns={"severity_class": "severity"})

    # Drop outcome columns that shouldn't be training features
    outcome_cols = ["admitted", "died", "admithos", "admit", "dieded", "los"]
    df = df.drop(columns=[c for c in outcome_cols if c in df.columns], errors="ignore")

    # Fill NaN with medians for numeric columns
    for col in df.select_dtypes(include=[np.number]).columns:
        if df[col].isna().any():
            median_val = df[col].median()
            df[col] = df[col].fillna(median_val)

    # Ensure severity is clean
    df = df.dropna(subset=["severity"])
    df["severity"] = df["severity"].astype(int)

    logger.info(
        "Pre-processed dataset ready: %d rows | Severity: %s",
        len(df),
        df["severity"].value_counts().sort_index().to_dict(),
    )
    return df


def _harmonize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Map existing dataset.csv columns to the standard feature names.

    Handles differences between prep_dataset.py output and our feature set:
      - 'diabetes' → 'diabetes_type2' (most common type in NHAMCS)
      - Missing columns filled with 0
    """
    # Column renames for compatibility
    rename_map = {
        "diabetes": "diabetes_type2",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    # Ensure all expected chronic condition columns exist
    for col in CHRONIC_CONDITION_COLS:
        if col not in df.columns:
            df[col] = 0

    # Ensure triage indicators exist
    for col in ["immediate_triage", "arrival_by_ems"]:
        if col not in df.columns:
            df[col] = 0

    # Ensure vitals exist
    for col in ["pain_scale", "respiratory_rate"]:
        if col not in df.columns:
            df[col] = 0.0

    return df


def load_nhamcs_raw(filepath: Optional[str] = None) -> pd.DataFrame:
    """
    Load and preprocess the raw NHAMCS 2022 ED data (ed2022.csv).

    This performs full preprocessing from scratch:
      1. Read CSV
      2. Rename columns
      3. Replace coded missing values with NaN
      4. Clean demographics / vitals
      5. Derive severity labels
      6. Compute engineered features
      7. Drop outcome columns

    Returns
    -------
    pd.DataFrame ready for model training (features + severity).
    """
    path = Path(filepath or DEFAULT_RAW_NHAMCS_PATH)
    if not path.exists():
        raise FileNotFoundError(
            f"Raw NHAMCS data file not found at '{path}'. "
            f"Place ed2022.csv in app/ai/ directory."
        )

    logger.info("Loading raw NHAMCS data from %s", path)
    raw = pd.read_csv(path, low_memory=False)
    logger.info("Raw NHAMCS rows: %d, columns: %d", len(raw), len(raw.columns))

    # Normalize column names to uppercase
    raw.columns = raw.columns.str.upper().str.strip()

    # NHAMCS column → Kyro column mapping
    nhamcs_col_map = {
        "AGE": "age",
        "SEX": "gender",
        "TEMPF": "temperature",
        "PULSE": "heart_rate",
        "RESPR": "respiratory_rate",
        "BPSYS": "systolic_bp",
        "BPDIAS": "diastolic_bp",
        "PAINSCALE": "pain_scale",
        "IMMEDR": "immediate_triage",
        "ARREMS": "arrival_by_ems",
        # Chronic conditions
        "ASTHMA": "asthma", "CANCER": "cancer", "CKD": "ckd",
        "COPD": "copd", "CHF": "chf", "CAD": "cad",
        "DIABTYP1": "diabetes_type1", "DIABTYP2": "diabetes_type2",
        "ESRD": "esrd", "HTN": "htn", "OBESITY": "obesity", "OSA": "osa",
        # Outcome columns (for labeling)
        "ADMITHOS": "admithos", "ADMIT": "admit",
        "DIEDED": "dieded", "LOS": "los",
    }

    needed_upper = set(nhamcs_col_map.keys())
    available = needed_upper & set(raw.columns)
    missing = needed_upper - available
    if missing:
        logger.warning("Missing NHAMCS columns: %s", missing)

    df = raw[list(available)].copy()
    df = df.rename(columns=nhamcs_col_map)

    # Replace NHAMCS coded missing values
    missing_codes = {-7, -8, -9, 998, 999, 9998, 9999}
    for col in df.select_dtypes(include=[np.number]).columns:
        df[col] = df[col].replace(list(missing_codes), np.nan)

    # Gender: NHAMCS 1=Female, 2=Male → 0=Female, 1=Male
    if "gender" in df.columns:
        df["gender"] = df["gender"].map({1: 0, 2: 1}).fillna(0).astype(int)

    # Clamp vitals to plausible ranges
    _clamp_vitals(df)

    # Chronic conditions → binary
    for col in CHRONIC_CONDITION_COLS:
        if col in df.columns:
            df[col] = df[col].clip(0, 1).fillna(0).astype(int)
        else:
            df[col] = 0

    # Triage indicators → binary
    for col in ["immediate_triage", "arrival_by_ems"]:
        if col in df.columns:
            df[col] = df[col].clip(0, 1).fillna(0).astype(int)
        else:
            df[col] = 0

    # Derive severity labels
    df = _derive_severity_labels(df)

    # Drop outcome columns
    outcome_cols = ["admithos", "admit", "dieded", "los"]
    df.drop(columns=[c for c in outcome_cols if c in df.columns], inplace=True)

    # Compute engineered features
    df = compute_engineered_features(df)

    # Fill NaN with medians
    for col in df.select_dtypes(include=[np.number]).columns:
        if df[col].isna().any():
            df[col] = df[col].fillna(df[col].median())

    df = df.dropna(subset=["severity"])
    df["severity"] = df["severity"].astype(int)

    logger.info(
        "NHAMCS raw preprocessed: %d rows | Severity: %s",
        len(df), df["severity"].value_counts().sort_index().to_dict(),
    )
    return df


def _clamp_vitals(df: pd.DataFrame) -> None:
    """Replace out-of-range vitals with NaN."""
    ranges = {
        "age": (0, 120),
        "temperature": (90.0, 110.0),
        "heart_rate": (30, 220),
        "respiratory_rate": (4, 60),
        "systolic_bp": (60, 250),
        "diastolic_bp": (30, 150),
        "pain_scale": (0, 10),
    }
    for col, (lo, hi) in ranges.items():
        if col in df.columns:
            mask = (df[col] < lo) | (df[col] > hi)
            df.loc[mask, col] = np.nan


def _derive_severity_labels(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create severity (0–3) from NHAMCS outcome variables + vitals.

    Critical (3): DIEDED==1 OR IMMEDR==1 OR SBP<80 OR shock_index>1.3
    High (2):     ADMITHOS==1 OR (CHF/CAD + abnormal vitals) OR chronic_burden>=3
    Medium (1):   Shock index 1.0–1.3 OR moderate pain
    Low (0):      Everything else
    """
    n = len(df)
    severity = np.zeros(n, dtype=int)

    si = np.where(df["systolic_bp"] > 0, df["heart_rate"] / df["systolic_bp"], 0.0)

    chronic_cols_present = [c for c in CHRONIC_CONDITION_COLS if c in df.columns]
    chronic_burden = df[chronic_cols_present].sum(axis=1).values

    # Critical (3)
    crit = np.zeros(n, dtype=bool)
    if "dieded" in df.columns:
        crit |= (df["dieded"].fillna(0) == 1).values
    if "immediate_triage" in df.columns:
        crit |= (df["immediate_triage"].fillna(0) == 1).values
    crit |= (df["systolic_bp"].fillna(999) < 80).values
    crit |= (si > 1.3)
    severity[crit] = 3

    # High (2)
    high = np.zeros(n, dtype=bool)
    if "admithos" in df.columns:
        high |= (df["admithos"].fillna(0) == 1).values
    heart_cond = np.zeros(n, dtype=bool)
    if "chf" in df.columns:
        heart_cond |= (df["chf"] == 1).values
    if "cad" in df.columns:
        heart_cond |= (df["cad"] == 1).values
    abnormal = (
        (df["heart_rate"].fillna(80) > 110) |
        (df["systolic_bp"].fillna(120) > 160) |
        (df["temperature"].fillna(98.6) > 101.5)
    ).values
    high |= (heart_cond & abnormal)
    high |= (chronic_burden >= 3)
    severity[high & (severity == 0)] = 2

    # Medium (1)
    med = np.zeros(n, dtype=bool)
    med |= ((si >= 1.0) & (si <= 1.3))
    med |= ((df["pain_scale"].fillna(0) >= 5) & (df["pain_scale"].fillna(0) < 8)).values
    severity[med & (severity == 0)] = 1

    df["severity"] = severity
    return df
